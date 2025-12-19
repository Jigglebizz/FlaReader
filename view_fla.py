import sys
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QMainWindow, QScrollArea
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6 import QtCore
from flafile import FlaFile, FlaShape, FlaStraightEdge

import pdb

class FlaSceneWidget( QWidget ):
  def __init__( self, fla : FlaFile ) -> None:
    super().__init__()

    self.fla = fla
    self.scene_idx = 0

    self.setFixedSize( fla.width, fla.height )

  def paintEvent( self, evt ) -> None:
    painter : QPainter = QPainter( self )
    painter.setRenderHint( QPainter.RenderHint.Antialiasing )
    painter.fillRect( self.rect(), QColor( self.fla.backgroundColor ) )

    for layer in self.fla.timelines[ self.scene_idx ].layers:
      if len( layer.frames ) > 0:
        frame : FlaFile.Frame = layer.frames[0]
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

    self.scene_select_combo.currentIndexChanged.connect( self.scene_index_changed )

    controls_widget : QWidget = QWidget()
    controls_layout : QHBoxLayout = QHBoxLayout()

    controls_widget.setLayout( controls_layout )
    controls_layout.addWidget( self.scene_select_combo ) 

    main_layout : QVBoxLayout = QVBoxLayout()
    main_layout.addWidget( scene_scroll_area )
    main_layout.addWidget( controls_widget )
    central_widget : QWidget = QWidget( )
    central_widget.setLayout( main_layout )
    self.setCentralWidget( central_widget )

  def scene_index_changed( self, value ) -> None:
    self.scene.scene_idx = value
    self.scene.repaint()