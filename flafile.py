import zipfile
import re
import xml.etree.ElementTree as ET
from flaedge import ReadFlaEdges, FlaEdge
from pathlib import Path
from typing import List, Tuple

import pdb

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
      self.color = entry_et.attrib[ 'color' ] if 'color' in entry_et.attrib else '#000000'
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

    fill = solid_stroke.find( f'{{{ns}}}fill' )
    if fill is not None:
      solid_color = fill.find( f'{{{ns}}}SolidColor' )
      if solid_color is not None:
        self.color : str = solid_color.attrib[ 'color' ] if 'color' in solid_color.attrib else '#000000'

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

    self.edges = ReadFlaEdges( shape_et, ns )

#------------------------------------------------------------------------------------------------
class FlaMovie:
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
      self.current    : bool = bool( layer_et.attrib[ 'current' ] ) if 'current' in layer_et.attrib else False
      self.isSelected : bool = bool( layer_et.attrib[ 'isSelected' ] ) if 'isSelected' in layer_et.attrib else False
      self.autoNamed  : bool = bool( layer_et.attrib[ 'autoNamed' ] ) if 'autoNamed' in layer_et.attrib else True
      self.frames     : List[ FlaMovie.Frame ] = []

      frames = layer_et.find( f'{{{ns}}}frames' )
      if frames is not None:
        for frame in frames:
          self.frames.append( FlaMovie.Frame( frame, ns ) )

      self.frames.sort(key=lambda f: f.index)

  class Timeline:
    def __init__( self, timeline_et : ET, ns : str ) -> None:
      self.name              : str  = timeline_et.attrib[ 'name' ]
      self.layerDepthEnabled : bool = bool( timeline_et.attrib[ 'layerDepthEnabled' ] )
      self.layers            : List[ FlaMovie.Layer ] = []

      layers = timeline_et.find( f'{{{ns}}}layers' )
      if layers is not None:
        for layer in layers:
          self.layers.append( FlaMovie.Layer( layer, ns ) )

  def __init__( self, fla_archive : zipfile.ZipFile, file_path : str ):
    dom_doc_str = fla_archive.read( file_path )
    self.doc = ET.fromstring( dom_doc_str )

    root_tag = self.doc.tag
    m = re.search( r'\{(.*)\}(DOMDocument|DOMSymbolItem)', root_tag )
    self.xml_namespace = m.group(1)

#------------------------------------------------------------------------------------------------
class FlaFile( FlaMovie ):
  class PlayOptions:
    def __init__( self, fla_doc : ET ) -> None:
      self.playLoop         : bool = bool( fla_doc.attrib[ 'playOptionsPlayLoop' ] )
      self.playPages        : bool = bool( fla_doc.attrib[ 'playOptionsPlayPages' ] )
      self.playFrameActions : bool = bool( fla_doc.attrib[ 'playOptionsPlayFrameActions' ] )


  def __init__( self, path : Path ) -> None:
    with zipfile.ZipFile( path.absolute(), 'r', is_adobe=True ) as fla_archive:
      super().__init__( fla_archive, 'DOMDocument.xml' )

      library_prefix = 'LIBRARY/'
      symbol_file_list : List[ str ] = \
        [ f for f in fla_archive.namelist() 
          if f.startswith( library_prefix ) and len( f ) > len( library_prefix ) 
        ]

      self.symbols = { symbol_file.removeprefix( library_prefix ).removesuffix('.xml'): 
                       FlaSymbol( fla_archive, symbol_file ) 
                       for symbol_file in symbol_file_list }

      self.path              : Path  = path
      self.backgroundColor   : str   = self.doc.attrib[ 'backgroundColor' ] if 'backgroundColor' in self.doc.attrib.keys() else '#ffffff'
      self.width             : int   = int( self.doc.attrib[ 'width' ] )
      self.height            : int   = int( self.doc.attrib[ 'height' ] ) if 'height' in self.doc.attrib.keys() else self.width
      self.frameRate         : int   = int( self.doc.attrib[ 'frameRate' ] )
      self.currentTimeline   : int   = int( self.doc.attrib[ 'currentTimeline' ] )
      self.creatorInfo       : str   = self.doc.attrib[ 'creatorInfo' ]
      self.platform          : str   = self.doc.attrib[ 'platform' ]
      self.versionInfo       : str   = self.doc.attrib[ 'versionInfo' ]
      self.majorVersion      : int   = int( self.doc.attrib[ 'majorVersion' ] )
      self.buildNumer        : int   = int( self.doc.attrib[ 'buildNumber' ] )
      self.viewAngle3D       : float = float( self.doc.attrib[ 'viewAngle3D' ] )
      self.vanishingPoint3DX : float = float( self.doc.attrib[ 'vanishingPoint3DX' ] ) 
      self.vanishingPoint3DY : float = float( self.doc.attrib[ 'vanishingPoint3DY' ] ) if 'vanishingPoint3DY' in self.doc.attrib.keys() else self.vanishingPoint3DX
      self.rulerUnitType     : str   = self.doc.attrib[ 'rulerUnitType' ] if 'rulerUnitType' in self.doc.attrib.keys() else 'points'
      self.nextSceneId       : int   = int( self.doc.attrib[ 'nextSceneIdentifier' ] )
      self.fileTypeGuid      : str   = self.doc.attrib[ 'filetypeGUID' ]
      self.fileGUID          : str   = self.doc.attrib[ 'fileGUID' ]

      self.playOptions : FlaFile.PlayOptions = FlaFile.PlayOptions( self.doc )

      self.timelines : List[ FlaMovie.Timeline ] = []
      timelines = self.doc.find( f'{{{self.xml_namespace}}}timelines' )

      if timelines is not None:
        for timeline in timelines:
          self.timelines.append( FlaMovie.Timeline( timeline, self.xml_namespace ) )

#------------------------------------------------------------------------------------------------
class FlaSymbol(FlaMovie):
  def __init__( self, fla_archive : zipfile.ZipFile, file_path : str ):
    super().__init__( fla_archive, file_path )

    timeline = self.doc.find( f'{{{ self.xml_namespace }}}timeline' )
    if timeline is not None:
      self.timeline = FlaMovie.Timeline( list( timeline )[0], self.xml_namespace )