import zipfile
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple

import pdb

#------------------------------------------------------------------------------------------------
class FlaEdge:
  def __init__( self, fill_style : int, stroke_style : int ):
    self.fillStyle1  = fill_style
    self.strokeStyle = stroke_style

#------------------------------------------------------------------------------------------------
class FlaStraightEdge(FlaEdge):
  def __init__( self, fill_style: int, stroke_style : int, point_a : Tuple[ int, int ], point_b : Tuple[ int, int ] ) -> None:
    super().__init__( fill_style, stroke_style)
    self.pointA = point_a
    self.pointB = point_b


#------------------------------------------------------------------------------------------------
class FlaMatrix:
  def __init__( self, mat_et : ET = None ) -> None:
    self.a  : float = float(mat_et.attrib[ 'a' ])  if mat_et is not None and 'a'  in mat_et.attrib.keys() else 0.0
    self.b  : float = float(mat_et.attrib[ 'b' ])  if mat_et is not None and 'b'  in mat_et.attrib.keys() else 0.0
    self.c  : float = float(mat_et.attrib[ 'c' ])  if mat_et is not None and 'c'  in mat_et.attrib.keys() else 0.0
    self.d  : float = float(mat_et.attrib[ 'd' ])  if mat_et is not None and 'd'  in mat_et.attrib.keys() else 0.0
    self.tx : float = float(mat_et.attrib[ 'tx' ]) if mat_et is not None and 'tx' in mat_et.attrib.keys() else 0.0
    self.ty : float = float(mat_et.attrib[ 'ty' ]) if mat_et is not None and 'ty' in mat_et.attrib.keys() else 0.0

#------------------------------------------------------------------------------------------------
class FlaFillStyle:
  def __init__( self, fill_et : ET ) -> None:
    self.index : int = int(fill_et.attrib[ 'index' ])

#------------------------------------------------------------------------------------------------
class FlaFillStyleSolidColor( FlaFillStyle ):
  def __init__( self, fill_et : ET, ns : str, default_color : str = '#000000') -> None:
    super().__init__( fill_et )
    solid_color_et = fill_et.find(f'{{{ns}}}SolidColor')
    self.color : str = solid_color_et.attrib[ 'color' ] if 'color' in solid_color_et.attrib else default_color

#------------------------------------------------------------------------------------------------
class FlaFillStyleGradient( FlaFillStyle ):
  class Entry:
    def __init__( self, entry_et : ET ) -> None:
      self.color = entry_et.attrib[ 'color' ]
      self.ratio = float(entry_et.attrib[ 'ratio' ] )

  def __init__( self, fill_et : ET, ns : str ) -> None:
    super().__init__( fill_et )    

  def _InitMatrix( self, gradient_type_et : ET, ns : str ) -> None:
    matrix_et   = gradient_type_et.find( f'{{{ns}}}matrix' )
    self.matrix = FlaMatrix( matrix_et.find( f'{{{ns}}}Matrix' ) ) if matrix_et is not None else FlaMatrix()

  def _InitEntries( self, gradient_type_et : ET, ns : str ) -> None:
    self.entries : List[ FlaFillStyleGradient.Entry ] = []
    for entry in gradient_type_et.findall( f'{{{ns}}}GradientEntry' ):
      self.entries.append( FlaFillStyleGradient.Entry( entry ) )

#------------------------------------------------------------------------------------------------
class FlaFillStyleLinearGradient( FlaFillStyleGradient ):
  def __init__( self, fill_et : ET, ns : str ) -> None:
    super().__init__( fill_et, ns )

    linear_gradient_et = fill_et.find( f'{{{ns}}}LinearGradient' )

    self._InitMatrix( linear_gradient_et, ns )
    self._InitEntries( linear_gradient_et, ns )

#------------------------------------------------------------------------------------------------
class FlaFillStyleRadialGradient( FlaFillStyleGradient ):
  def __init__( self, fill_et : ET, ns : str ) -> None:
    super().__init__( fill_et, ns )

    radial_gradient_et : ET = fill_et.find( f'{{{ns}}}RadialGradient' )

    self.focalPointRatio : float = float( radial_gradient_et.attrib[ 'focalPointRatio' ] ) if 'focalPointRatio' in radial_gradient_et.attrib else 0.0

    self._InitMatrix( radial_gradient_et, ns )
    self._InitEntries( radial_gradient_et, ns )


#------------------------------------------------------------------------------------------------
class FlaStrokeStyle:
  def __init__( self, stroke_et : ET ) -> None:
    self.index : int = int( stroke_et.attrib[ 'index' ] )

#------------------------------------------------------------------------------------------------
class FlaStrokeStyleSolid(FlaStrokeStyle):
  def __init__( self, stroke_et : ET, ns : str ) -> None:
    super().__init__( stroke_et )
    solid_stroke    : ET  = stroke_et.find( f'{{{ns}}}SolidStroke' )
    self.scaleMode  : str = solid_stroke.attrib[ 'scaleMode' ] if 'scaleMode' in solid_stroke.attrib else 'normal'
    self.joints     : str = solid_stroke.attrib[ 'joints' ] if 'joints' in solid_stroke.attrib else 'miter'
    self.miterLimit : int = int( solid_stroke.attrib[ 'miterLimit' ] ) if 'miterLimit' in solid_stroke.attrib else 3

    fill = stroke_et.find( f'{{{ns}}}fill' )
    if fill is not None:
      if fill.find( f'{{{ns}}}SolidColor' ) != None:
        self.fill = FlaFillStyleSolidColor( fill, ns, default_color='#000000' )

#------------------------------------------------------------------------------------------------
class FlaElement:
  def __init__( self ):
    pass

#------------------------------------------------------------------------------------------------
class FlaShape(FlaElement):
  def __init__( self, shape_et : ET, ns : str ) -> None:
    self.fills : List[ FlaFillStyle ]  = []

    fills = shape_et.find( f'{{{ns}}}fills' )
    if fills is not None:
      for fill in fills.findall( f'{{{ns}}}FillStyle' ):
        if fill.find( f'{{{ns}}}SolidColor' ) != None:
          self.fills.append( FlaFillStyleSolidColor( fill, ns, default_color='#ffffff' ) )
        elif fill.find( f'{{{ns}}}LinearGradient' ):
          self.fills.append( FlaFillStyleLinearGradient( fill, ns ) )
        elif fill.find( f'{{{ns}}}RadialGradient' ):
          self.fills.append( FlaFillStyleRadialGradient( fill, ns ) )

    self.fills.sort( key=lambda f: f.index )

    self.strokes : List[ FlaStrokeStyle ] = []
    strokes = shape_et.find( f'{{{ns}}}strokes' )
    if strokes is not None:
      for stroke in strokes.findall( f'{{{ns}}}StrokeStyle' ):
        if stroke.find( f'{{{ns}}}SolidStroke' ) != None:
          self.strokes.append( FlaStrokeStyleSolid( stroke, ns ) )

    self.edges = self.ReadEdges( shape_et, ns )

  def ReadEdges( self, shape_et : ET, ns : str ) -> List[ FlaEdge ]:
    fla_edges : List[ FlaEdge ] = []

    edges : ET = shape_et.find( f'{{{ns}}}edges' )
    if edges is not None:
      for edge in edges.findall( f'{{{ns}}}Edge' ):
        if 'edges' in edge.attrib: # for now, ignore cubic descriptions
          fill_style_idx   : int = int(edge.attrib['fillStyle1']) if 'fillStyle1' in edge.attrib else -1
          stroke_style_idx : int = int(edge.attrib['strokeStyle']) if 'strokeStyle' in edge.attrib else -1
  
          edge_descs = edge.attrib['edges'].split('!')
          edge_descs = [ e for e in edge_descs if len(e) > 0 ]
          for e in edge_descs:
            straight_match = re.search( r'(\-?\d+) (\-?\d+)\|(\-?\d+) (\-?\d+)', e )
            if straight_match is not None:
              fla_edges.append( FlaStraightEdge( fill_style_idx, stroke_style_idx, \
                                                ( int( straight_match.group(1) ), int( straight_match.group(2) ) ), \
                                                ( int( straight_match.group(3) ), int( straight_match.group(4) ) ) \
                                               ) )
    return fla_edges

#------------------------------------------------------------------------------------------------
class FlaFile:
  class PlayOptions:
    def __init__( self, fla_doc : ET ) -> None:
      self.playLoop         : bool = bool( fla_doc.attrib[ 'playOptionsPlayLoop' ] )
      self.playPages        : bool = bool( fla_doc.attrib[ 'playOptionsPlayPages' ] )
      self.playFrameActions : bool = bool( fla_doc.attrib[ 'playOptionsPlayFrameActions' ] )

  class Frame:
    def __init__( self, frame_et : ET, ns : str ) -> None:
      self.index   : int = int( frame_et.attrib[ 'index' ] )

      # todo: look up actual key mode as an enum
      self.keyMode : int = int( frame_et.attrib[ 'keyMode' ] )

      self.elements : List[ FlaElement ] = []
      elements = frame_et.find( f'{{{ns}}}elements' )
      if elements is not None:
        for element in elements.findall(f'{{{ns}}}DOMShape'):
          self.elements.append( FlaShape( element, ns ) )

  class Layer:
    def __init__( self, layer_et : ET, ns : str ) -> None:
      self.name       : str  = layer_et.attrib[ 'name' ]
      self.color      : str  = layer_et.attrib[ 'color' ]
      self.current    : bool = bool( layer_et.attrib[ 'current' ] )
      self.isSelected : bool = bool( layer_et.attrib[ 'isSelected' ] )
      self.autoNamed  : bool = bool( layer_et.attrib[ 'autoNamed' ] ) if 'autoNamed' in layer_et.attrib else True
      self.frames     : List[ FlaFile.Frame ] = []

      frames = layer_et.find( f'{{{ns}}}frames' )
      if frames is not None:
        for frame in frames:
          self.frames.append( FlaFile.Frame( frame, ns ) )

      self.frames.sort(key=lambda f: f.index)

  class Timeline:
    def __init__( self, timeline_et : ET, ns : str ) -> None:
      self.name              : str  = timeline_et.attrib[ 'name' ]
      self.layerDepthEnabled : bool = bool( timeline_et.attrib[ 'layerDepthEnabled' ] )
      self.layers            : List[ FlaFile.Layer ] = []

      layers = timeline_et.find( f'{{{ns}}}layers' )
      if layers is not None:
        for layer in layers:
          self.layers.append( FlaFile.Layer( layer, ns ) )


  def __init__( self, path : Path ) -> None:
    with zipfile.ZipFile( path.absolute(), 'r', is_adobe=True ) as fla_archive:
      dom_doc_str = fla_archive.read( 'DOMDocument.xml' )
      fla_doc = ET.fromstring( dom_doc_str )

      root_tag = fla_doc.tag
      m = re.search( '\{(.*)\}DOMDocument', root_tag )
      ns = m.group(1)

      self.path              : Path  = path
      self.backgroundColor   : str   = fla_doc.attrib[ 'backgroundColor' ] if 'backgroundColor' in fla_doc.attrib.keys() else '#ffffff'
      self.width             : int   = int( fla_doc.attrib[ 'width' ] )
      self.height            : int   = int( fla_doc.attrib[ 'height' ] )
      self.frameRate         : int   = int( fla_doc.attrib[ 'frameRate' ] )
      self.currentTimeline   : int   = int( fla_doc.attrib[ 'currentTimeline' ] )
      self.creatorInfo       : str   = fla_doc.attrib[ 'creatorInfo' ]
      self.platform          : str   = fla_doc.attrib[ 'platform' ]
      self.versionInfo       : str   = fla_doc.attrib[ 'versionInfo' ]
      self.majorVersion      : int   = int( fla_doc.attrib[ 'majorVersion' ] )
      self.buildNumer        : int   = int( fla_doc.attrib[ 'buildNumber' ] )
      self.viewAngle3D       : float = float( fla_doc.attrib[ 'viewAngle3D' ] )
      self.vanishingPoint3DX : float = float( fla_doc.attrib[ 'vanishingPoint3DX' ] )
      self.vanishingPoint3DY : float = float( fla_doc.attrib[ 'vanishingPoint3DY' ] )
      self.rulerUnitType     : str   = fla_doc.attrib[ 'rulerUnitType' ] if 'rulerUnitType' in fla_doc.attrib.keys() else 'points'
      self.nextSceneId       : int   = int( fla_doc.attrib[ 'nextSceneIdentifier' ] )
      self.fileTypeGuid      : str   = fla_doc.attrib[ 'filetypeGUID' ]
      self.fileGUID          : str   = fla_doc.attrib[ 'fileGUID' ]

      self.playOptions : FlaFile.PlayOptions = FlaFile.PlayOptions( fla_doc )
      
      self.timelines : List[ FlaFile.Timeline ] = []
      timelines = fla_doc.find( f'{{{ns}}}timelines' )

      if timelines is not None:
        for timeline in timelines:
          self.timelines.append( FlaFile.Timeline( timeline, ns ) )