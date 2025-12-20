import sys
from enum import Enum
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QMainWindow, QScrollArea, QLineEdit, QPushButton
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPolygonF, QIntValidator
from PyQt6.QtCore import Qt, QPointF, QLineF, QObject, pyqtSignal, pyqtSlot
from flafile import FlaFile, FlaShape, FlaStraightEdge

import pdb

#------------------------------------------------------------------------------
class FlaSceneWidget( QWidget ):
  def __init__( self, fla : FlaFile ) -> None:
    super().__init__()

    self.fla = fla
    self.scene_idx = 0
    self.frame_idx = 0

    self.setFixedSize( fla.width, fla.height )

  def paintEvent( self, evt ) -> None:
    painter : QPainter = QPainter( self )
    painter.setRenderHint( QPainter.RenderHint.Antialiasing )
    painter.fillRect( self.rect(), QColor( self.fla.backgroundColor ) )

    for layer in self.fla.timelines[ self.scene_idx ].layers:
      if len( layer.frames ) > 0:
        frame : FlaFile.Frame = layer.frames[ self.frame_idx ]
        for element in frame.elements:
          if isinstance( element, FlaShape ):
            shape : FlaShape = element
            default_pen = QPen( QColor( '#000000' ), 1.0 )
            for edge in shape.edges:
              painter.setPen( default_pen )

              straight_edge : FlaStraightEdge = edge
              qline : QLineF = QLineF( QPointF(straight_edge.pointA[0] / 20.0, straight_edge.pointA[1] / 20.0), 
                                       QPointF(straight_edge.pointB[0] / 20.0, straight_edge.pointB[1] / 20.0) )
              painter.drawLine( qline )

#------------------------------------------------------------------------------
class FlaTransportModel( QObject ):
  frameChanged = pyqtSignal( int )

  Mode = Enum(
  'Mode',
  [
    'Playing',
    'Paused'
  ])

  def __init__( self, timeline: FlaFile.Timeline ):
    super().__init__()
    self.frame_idx = 0
    self.frame_max = self.getMaxFramesInTimeline( timeline )
    self.mode      = FlaTransportModel.Mode.Paused

  @pyqtSlot()
  def getMaxFramesInTimeline( self, timeline : FlaFile.Timeline ) -> int :
    max_len = 0
    for layer in timeline.layers:
      max_len = max( max_len, layer.frames[-1].index )
    return max_len

  @pyqtSlot()
  def advanceOneFrame( self ) -> None:
    self.frame_idx = self.frame_max if self.frame_idx == self.frame_max else self.frame_idx + 1
    self.mode      = FlaTransportModel.Mode.Paused
    self.frameChanged.emit( self.frame_idx )

  @pyqtSlot()
  def goBackOneFrame( self ) -> None:
    self.frame_idx = 0 if self.frame_idx == 0 else self.frame_idx - 1
    self.mode      = FlaTransportModel.Mode.Paused
    self.frameChanged.emit( self.frame_idx )

  @pyqtSlot()
  def goToEnd( self ) -> None:
    self.frame_idx = self.frame_max
    self.mode      = FlaTransportModel.Mode.Paused
    self.frameChanged.emit( self.frame_idx )

  @pyqtSlot()
  def goToBeginning( self ):
    self.frame_idx = 0
    self.mode      = FlaTransportModel.Mode.Paused
    self.frameChanged.emit( self.frame_idx )

  @pyqtSlot()
  def play( self ) -> None:
    pass

  @pyqtSlot()
  def pause( self ) -> None:
    pass

  @pyqtSlot()
  def setTimeline( self, timeline: FlaFile.Timeline ):
    self.frame_max = self.getMaxFramesInTimeline( timeline )
    self.frame_idx = 0
    self.mode      = FlaTransportModel.Mode.Paused
    self.frameChanged.emit( self.frame_idx )

  @pyqtSlot()
  def setFrame( self, value : int ) -> None:
    self.frame_idx = value
    self.frameChanged.emit( self.frame_idx )

#------------------------------------------------------------------------------
class FlaFrameSelectWidget( QWidget ):
  frameChanged : pyqtSignal = pyqtSignal(int)

  def __init__( self, name: str, transport_model : FlaTransportModel ):
    super().__init__()

    self.line_edit : QLineEdit = QLineEdit()
    self.line_edit.setMaximumWidth( 80 )
    self.max_label : QLabel = QLabel()
    self.transport_model : FlaTransportModel = transport_model
    
    frame_display_widget : QWidget     = QWidget()
    frame_display_layout : QHBoxLayout = QHBoxLayout()

    frame_display_widget.setLayout( frame_display_layout )
    frame_display_layout.addWidget( self.line_edit )
    frame_display_layout.addWidget( self.max_label )

    top_layout : QVBoxLayout = QVBoxLayout()
    self.setLayout( top_layout )
    top_layout.addWidget( QLabel( name ) )
    top_layout.addWidget( frame_display_widget )

    self.onModelChanged()
    self.line_edit.textEdited.connect( self.onTextEdited )
    self.frameChanged.connect( self.transport_model.setFrame )
    self.transport_model.frameChanged.connect( self.onFrameChanged )
  
  def onModelChanged( self ) -> None:
    self.line_edit.setValidator( QIntValidator( 0, self.transport_model.frame_max ) )
    self.line_edit.setText( '0' )
    self.max_label.setText( f'/ {self.transport_model.frame_max}' )

  def onTextEdited(self, value : str ) -> None:
    if len(value) > 0:
      val = int(value)
      if val > self.transport_model.frame_max:
        val = self.transport_model.frame_max
      self.line_edit.setText( str( val ) )
      self.frameChanged.emit( val )

  def onFrameChanged( self, value : int ) -> None:
    if value > self.transport_model.frame_max:
      value = self.transport_model.frame_max
    self.line_edit.setText( str( value ) )

#------------------------------------------------------------------------------
class FlaTransportWidget( QWidget ):
  def __init__( self, transport_model : FlaTransportModel ):
    super().__init__()
    
    self.transport_model = transport_model

    rewind_button            : QPushButton = QPushButton('|<')
    back_one_frame_button    : QPushButton = QPushButton( '<<' )
    play_button              : QPushButton = QPushButton( '>' )
    advance_one_frame_button : QPushButton = QPushButton( '>>' )
    last_frame_button        : QPushButton = QPushButton( '>|' )

    layout : QHBoxLayout = QHBoxLayout()

    self.setLayout( layout )
    layout.addWidget( rewind_button )
    layout.addWidget( back_one_frame_button )
    layout.addWidget( play_button )
    layout.addWidget( advance_one_frame_button )
    layout.addWidget( last_frame_button )

    rewind_button.clicked.connect           ( self.transport_model.goToBeginning )
    back_one_frame_button.clicked.connect   ( self.transport_model.goBackOneFrame )
    play_button.clicked.connect             ( self.transport_model.play )
    advance_one_frame_button.clicked.connect( self.transport_model.advanceOneFrame )
    last_frame_button.clicked.connect       ( self.transport_model.goToEnd )

#------------------------------------------------------------------------------
class QtFlaWindow( QMainWindow ):
  def __init__( self, fla : FlaFile ):
    super().__init__()

    self.fla = fla
    self.setWindowTitle( str( fla.path.absolute() ) )
  
    self.scene : FlaSceneWidget = FlaSceneWidget( fla )

    scene_scroll_area : QScrollArea = QScrollArea()
    scene_scroll_area.setWidget( self.scene )
    
    self.scene_select_combo : QComboBox = QComboBox()

    for timeline in fla.timelines:
      self.scene_select_combo.addItem( timeline.name )

    self.transport_model : FlaTransportModel = FlaTransportModel( fla.timelines[ 0 ] )

    self.transport    : FlaTransportWidget   = FlaTransportWidget( self.transport_model )
    self.frame_select : FlaFrameSelectWidget = FlaFrameSelectWidget( 'Frame Select', self.transport_model )

    controls_widget : QWidget = QWidget()
    controls_layout : QHBoxLayout = QHBoxLayout()

    controls_widget.setLayout( controls_layout )
    controls_layout.addWidget( self.scene_select_combo )
    controls_layout.addWidget( self.transport )
    controls_layout.addWidget( self.frame_select )

    main_layout : QVBoxLayout = QVBoxLayout()
    main_layout.addWidget( scene_scroll_area )
    main_layout.addWidget( controls_widget )
    central_widget : QWidget = QWidget( )
    central_widget.setLayout( main_layout )
    self.setCentralWidget( central_widget )

    self.scene_select_combo.currentIndexChanged.connect( self.sceneIndexChanged )
    self.transport_model.frameChanged.connect( self.onFrameChanged )

  def sceneIndexChanged( self, value ) -> None:
    self.scene.scene_idx = value
    self.scene.frame_idx = 0
    self.frame_select.setTimeline( self.fla.timelines[ value ] )
    self.scene.repaint()

  def onFrameChanged( self, value ) -> None:
    self.scene.frame_idx = value
    self.scene.repaint()