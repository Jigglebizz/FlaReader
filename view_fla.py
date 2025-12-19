import sys
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QMainWindow, QScrollArea, QLineEdit
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPolygonF, QIntValidator
from PyQt6.QtCore import Qt, QPointF, QLineF, pyqtSignal
from flafile import FlaFile, FlaShape, FlaStraightEdge

import pdb

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

class FlaFrameSelectWidget( QWidget ):
  frameChanged : pyqtSignal = pyqtSignal(int)

  def __init__( self, name: str, timeline: FlaFile.Timeline ):
    super().__init__()

    self.line_edit : QLineEdit = QLineEdit()
    self.line_edit.setMaximumWidth( 80 )
    self.max_label : QLabel = QLabel()

    self.setTimeline( timeline )
    
    frame_display_widget : QWidget     = QWidget()
    frame_display_layout : QHBoxLayout = QHBoxLayout()

    frame_display_widget.setLayout( frame_display_layout )
    frame_display_layout.addWidget( self.line_edit )
    frame_display_layout.addWidget( self.max_label )

    top_layout :QVBoxLayout = QVBoxLayout()
    self.setLayout( top_layout )
    top_layout.addWidget( QLabel( name ) )
    top_layout.addWidget( frame_display_widget )

    self.line_edit.textEdited.connect( self.onFrameChanged )

  def getMaxFramesInTimeline( self, timeline : FlaFile.Timeline ) -> int :
    max_len = 0
    for layer in timeline.layers:
      max_len = max( max_len, layer.frames[-1].index )
    return max_len
  
  def setTimeline( self, timeline : FlaFile.Timeline ) -> None:
    self.frame_max = self.getMaxFramesInTimeline( timeline )
    self.line_edit.setValidator( QIntValidator( 0, self.frame_max ) )
    self.line_edit.setText( '0' )
    self.max_label.setText( f'/ {self.frame_max}' )

  def onFrameChanged(self, value) -> None:
    if len(value) > 0:
      val = int(value)
      if val > self.frame_max:
        val = self.frame_max
        self.line_edit.setText( str( val ) )
      self.frameChanged.emit( val )

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

    self.frame_select : FlaFrameSelectWidget = FlaFrameSelectWidget( 'Frame Select', fla.timelines[ 0 ] )

    controls_widget : QWidget = QWidget()
    controls_layout : QHBoxLayout = QHBoxLayout()

    controls_widget.setLayout( controls_layout )
    controls_layout.addWidget( self.scene_select_combo )
    controls_layout.addWidget( self.frame_select )

    main_layout : QVBoxLayout = QVBoxLayout()
    main_layout.addWidget( scene_scroll_area )
    main_layout.addWidget( controls_widget )
    central_widget : QWidget = QWidget( )
    central_widget.setLayout( main_layout )
    self.setCentralWidget( central_widget )

    self.scene_select_combo.currentIndexChanged.connect( self.sceneIndexChanged )
    self.frame_select.frameChanged.connect( self.onFrameChanged )

  def sceneIndexChanged( self, value ) -> None:
    self.scene.scene_idx = value
    self.scene.frame_idx = 0
    self.frame_select.setTimeline( self.fla.timelines[ value ] )
    self.scene.repaint()

  def onFrameChanged( self, value ) -> None:
    self.scene.frame_idx = value
    self.scene.repaint()