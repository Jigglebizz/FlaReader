import re
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict
from enum import Enum

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
class FlaCubicEdge(FlaEdge):
  def __init__( self, fill_style: int, stroke_style: int, point_a : Tuple[ int, int ], point_b : Tuple[ int, int ], control_point_a : Tuple[ int, int ], control_point_b : Tuple[ int, int ] ):
    pass

#------------------------------------------------------------------------------------------------
class FlaPoint:
  def __init__( self, x : int, y : int ):
    self.x = x
    self.y = y

#------------------------------------------------------------------------------------------------
# intermediate representation for edges
class FlaEdgeDescription:
  Type = Enum(
  'Type',
  [
    'Straight',
    'Curved'
  ]
  )

  def __init__( self, syntax : str ):
    straight_re = r'(\-?\d+) (\-?\d+)\|(\-?\d+) (\-?\d+)'
    curve_re    = r'(\-?\d+) (\-?\d+)\[(\-?\d+) (\-?\d+) (\-?\d+) (\-?\d+)'

    straight_match = re.search( straight_re, syntax )
    curve_match    = re.search( curve_re,    syntax )

    if straight_match is not None:
      self.type  = FlaEdgeDescription.Type.Straight
      self.start = FlaPoint( int(straight_match.group(1)), int(straight_match.group(2)) )
      self.end   = FlaPoint( int(straight_match.group(3)), int(straight_match.group(4)) )
      self.id    = f'{straight_match.group(1)}{straight_match.group(2)}{straight_match.group(3)}{straight_match.group(4)}'

    elif curve_match is not None:
      self.type               = FlaEdgeDescription.Type.Curved
      self.start              = FlaPoint( int(curve_match.group(1)), int(curve_match.group(2)) )
      self.end                = FlaPoint( int(curve_match.group(5)), int(curve_match.group(6)) )
      self.bspline_control_pt = FlaPoint( int(curve_match.group(3)), int(curve_match.group(4)) )
      self.id                 = f'{curve_match.group(1)}{curve_match.group(2)}{curve_match.group(3)}{curve_match.group(4)}{curve_match.group(5)}{curve_match.group(6)}'
    else:
      raise Exception( f'Unrecognized edge description syntax: {syntax}' )

#------------------------------------------------------------------------------------------------
# intermediate representation for edge cubics
class FlaEdgeCubicDescription:
  class Replacement:
    def __init__( self, start_str : str, end_str : str ):
      start_with_bspline = start_str.split('Q')
      end_with_bspline   = end_str.split('Q')
      
      point_re = r'(\-?\d+) (\-?\d+)'
      start_match = re.search( point_re, start_with_bspline[0])
      end_match   = re.search( point_re, end_with_bspline  [0])

      if start_match is None:
        raise Exception( f'Unrecognized point syntax in edge replacement description: { start_with_bspline[0]}' )
      if end_match is None:
        raise Exception( f'Unrecognized point syntax in edge replacement description: { end_with_bspline[0]}' )

      self.start = FlaPoint( int(start_match.group(1)), int(start_match.group(2)) )
      self.end   = FlaPoint( int(end_match.group(1)),   int(end_match.group(2))   )

      if len( start_with_bspline ) > 1: # we have a control point to deal with
        bspline_match = re.search( point_re, start_with_bspline[ 1 ] )
        if bspline_match is None:
          raise Exception( f'Unrecognized point syntax for bspline in edge replacement description: { start_with_bspline[1] } ')
        

        self.bspline_control_point = FlaPoint( int(bspline_match.group(1)), int(bspline_match.group(2)) )
        self.id = f'{self.start.x}{self.start.y}{self.bspline_control_point.x}{self.bspline_control_point.y}{self.end.x}{self.end.y}'
      else:
        self.id = f'{self.start.x}{self.start.y}{self.end.x}{self.end.y}'

  def __init__( self, syntax : str ):
    cubic_re = r'\!(\-?\d+) (\-?\d+)\((.*)\)(\-?\d+),(\-?\d+);'

    cubic_match = re.search( cubic_re, syntax )
    if cubic_match is not None:
      self.start = FlaPoint( int(cubic_match.group(1)), int(cubic_match.group(2)) )
      self.end   = FlaPoint( int(cubic_match.group(4)), int(cubic_match.group(5)) )

      cubics_desc = cubic_match.group(3)

      # the cubics describe four control points for the two endpoints
      # this is followed by a list of points from the edge description that this single cubic curve is intended to replace
      cubics_re    = r'(\-?\d+),(\-?\d+);(\-?\d+),(\-?\d+) (\-?\d+),(\-?\d+) (\-?\d+),(\-?\d+)(.*)'
      cubics_match = re.search( cubics_re, cubics_desc )
      if cubics_match is not None:
        self.start_control_point_a = FlaPoint( int(cubics_match.group(1)), int(cubics_match.group(2)))
        self.start_control_point_b = FlaPoint( int(cubics_match.group(3)), int(cubics_match.group(4)))
        self.end_control_point_a   = FlaPoint( int(cubics_match.group(5)), int(cubics_match.group(6)))
        self.end_control_point_b   = FlaPoint( int(cubics_match.group(7)), int(cubics_match.group(8)))

        replacement_list = cubics_match.group(9)

        repl_edges = [ repl_edge for repl_edge in replacement_list.split( 'q' ) if len(repl_edge) > 0 ]

        self.replacements : List[ FlaEdgeCubicDescription.Replacement ] = []
        for i_repl in range(0, len(repl_edges) - 1 ):
          self.replacements.append( repl_edges[ i_repl ], repl_edges[ i_repl + 1 ] )
      else:
        raise Exception( f'Unrecognized cubics description syntax: {cubics_desc}' )
    else:
      raise Exception( f'Unrecognized cubic description syntax: {syntax}' )

#------------------------------------------------------------------------------------------------
def ReadFlaEdges( shape_et : ET, ns : str ) -> List[ FlaEdge ]:
  fla_edges : List[ FlaEdge ] = []

  edges : ET = shape_et.find( f'{{{ns}}}edges' )
  if edges is not None:

    # lookup from edge id to edge description
    edge_desc_lookup : Dict[ str, FlaEdgeDescription ] = []
    cubics_descs     : List[ FlaEdgeCubicDescription ] = []

    for edge in edges.findall( f'{{{ns}}}Edge' ):
      if 'edges' in edge.attrib:
        fill_style_idx   : int = int(edge.attrib['fillStyle1']) if 'fillStyle1' in edge.attrib else -1
        stroke_style_idx : int = int(edge.attrib['strokeStyle']) if 'strokeStyle' in edge.attrib else -1

        edge_desc_syntaxes = edge.attrib['edges'].split('!')
        edge_descs = [ FlaEdgeDescription( e ) for e in edge_desc_syntaxes if len(e) > 0 ]

        edge_desc_lookup = { e.id : e for e in edge_descs }
      elif 'cubics' in edge.attrib:
        cubics_descs.append( FlaEdgeCubicDescription( edge.attrib[ 'cubics' ] ) )

      # now that we have all the data to create our edges, lets do it
      

  return fla_edges
  
def ReadCubics() -> List[ FlaEdge ]:
  fla_edges : List[ FlaEdge ] = []
  
  return fla_edges