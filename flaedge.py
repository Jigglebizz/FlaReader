import re
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict
from enum import Enum

import pdb

#------------------------------------------------------------------------------------------------
class FlaEdge:
  def __init__( self, fill_style : int, stroke_style : int, point_a : Tuple[ float, float ], point_b : Tuple[ float, float ] ):
    self.fillStyle1  = fill_style
    self.strokeStyle = stroke_style
    self.pointA = point_a
    self.pointB = point_b

#------------------------------------------------------------------------------------------------
class FlaStraightEdge(FlaEdge):
  def __init__( self, fill_style: int, stroke_style : int, point_a : Tuple[ float, float ], point_b : Tuple[ float, float ] ) -> None:
    super().__init__( fill_style, stroke_style, point_a, point_b )

#------------------------------------------------------------------------------------------------
class FlaCubicEdge(FlaEdge):
  def __init__( self, fill_style: int, stroke_style: int, 
                      point_a : Tuple[ float, float ], 
                      point_b : Tuple[ float, float ], 
                      control_point_a1 : Tuple[ float, float ],
                      control_point_a2 : Tuple[ float, float ], 
                      control_point_b1 : Tuple[ float, float ], 
                      control_point_b2 : Tuple[ float, float ] ):
    super().__init__( fill_style, stroke_style, point_a, point_b )
    self.control_point_a1 = control_point_a1
    self.control_point_a2 = control_point_a2
    self.control_point_b1 = control_point_b1
    self.control_point_b2 = control_point_b2

#------------------------------------------------------------------------------------------------
class FlaQuadraticEdge(FlaEdge):
  def __init__( self, fill_style: int, stroke_style: int,
                      point_a : Tuple[ float, float ],
                      point_b : Tuple[ float, float ], 
                      control_point : Tuple[ float, float ] ):
    super().__init__( fill_style, stroke_style, point_a, point_b )
    self.control_point = control_point

#------------------------------------------------------------------------------------------------
class FlaPoint:
  def __init__( self, x : str, y : str ):
    int_regex      = r'^(\-?\d+(\.\d+)?)(S\d+)?$'
    fixed_pt_regex = r'^#([0-9A-F]+)\.([0-9A-F]+)$'

    int_match_x   = re.search( int_regex, x )
    fixed_match_x = re.search( fixed_pt_regex, x )
    int_match_y   = re.search( int_regex, y )
    fixed_match_y = re.search( fixed_pt_regex, y )

    if int_match_x is not None:
      self.x = float( int_match_x.group(1) )
    elif fixed_match_x is not None:
      self.x = float( f'{int( fixed_match_x.group(1), 16 )}.{int( fixed_match_x.group(2), 16)}' )
    else:
      raise Exception( f'Unrecognized syntax for coordinate: {x}' )
    
    if int_match_y is not None:
      self.y = float( int_match_y.group( 1 ) )
    elif fixed_match_y is not None:
      self.y = float( f'{int( fixed_match_y.group(1), 16 )}.{int( fixed_match_y.group(2), 16)}' )
    else:
      raise Exception( f'Unrecognized syntax for coordinate: {y}' )

#------------------------------------------------------------------------------------------------
# intermediate representation for edges
class FlaEdgeDescription:
  Type = Enum(
  'Type',
  [
    'Straight',
    'Quadratic'
  ]
  )

  def __init__( self, syntax : str, fill_style_idx : int, stroke_style_idx : int ):
    self.fill_style_idx   = fill_style_idx
    self.stroke_style_idx = stroke_style_idx

    straight_desc  = '|' in syntax or '/' in syntax
    quadratic_desc = '[' in syntax

    if straight_desc:
      syntax = syntax.replace( '|', ' ' )
      syntax = syntax.replace( '/', ' ' )

      nums : str = syntax.split( ' ' )

      if len( nums ) == 4:

        nums_itr                             = iter( nums )
        points   : List[ Tuple[ str, str ] ] = list( zip( nums_itr, nums_itr ) )
  
        self.type  = FlaEdgeDescription.Type.Straight
        self.start = FlaPoint( points[ 0 ][ 0 ], points[ 0 ][ 1 ] )
        self.end   = FlaPoint( points[ 1 ][ 0 ], points[ 1 ][ 1 ] )
      else:
        raise Exception( f'Unrecognized edge description syntax: {syntax}' )

    elif quadratic_desc:
      syntax = syntax.replace( '[', ' ' )

      nums : str = syntax.split( ' ' )

      if len( nums ) == 6:
        
        nums_itr                           = iter( nums )
        points : List[ Tuple[ str, str ] ] = list( zip( nums_itr, nums_itr ) )

        self.type          = FlaEdgeDescription.Type.Quadratic
        self.start         = FlaPoint( points[ 0 ][ 0 ], points[ 0 ][ 1 ])
        self.end           = FlaPoint( points[ 2 ][ 0 ], points[ 2 ][ 1 ] )
        self.control_point = FlaPoint( points[ 1 ][ 0 ], points[ 1 ][ 1 ] )
      else:
        raise Exception( f'Unrecognized edge description syntax: {syntax}')
    else:
      pdb.set_trace()
      raise Exception( f'Unrecognized edge description syntax: {syntax}' )

#------------------------------------------------------------------------------------------------
# intermediate representation for edge cubics
#class FlaEdgeCubicDescription:
#  class Replacement:
#    def __init__( self, start_str : str, end_str : str ):
#      start_with_bspline = start_str.split('Q')
#      end_with_bspline   = end_str.split('Q')
#      
#      point_re = re.compile(f'{ FlaPoint.point_regex } { FlaPoint.point_regex }')
#      start_match = re.search( point_re, start_with_bspline[0])
#      end_match   = re.search( point_re, end_with_bspline  [0])
#
#      if start_match is None:
#        raise Exception( f'Unrecognized point syntax in edge replacement description: { start_with_bspline[0]}' )
#      if end_match is None:
#        raise Exception( f'Unrecognized point syntax in edge replacement description: { end_with_bspline[0]}' )
#
#      self.start = FlaPoint( start_match.group(1), start_match.group(5) )
#      self.end   = FlaPoint( end_match.group(1),   end_match.group(5)   )
#
#      if len( start_with_bspline ) > 1: # we have a control point to deal with
#        bspline_match = re.search( point_re, start_with_bspline[ 1 ] )
#        if bspline_match is None:
#          raise Exception( f'Unrecognized point syntax for bspline in edge replacement description: { start_with_bspline[1] } ')
#        
#
#        self.bspline_control_point = FlaPoint( bspline_match.group(1), bspline_match.group(2) )
#        self.id = f'{self.start.x}{self.start.y}{self.bspline_control_point.x}{self.bspline_control_point.y}{self.end.x}{self.end.y}'
#      else:
#        self.id = f'{self.start.x}{self.start.y}{self.end.x}{self.end.y}'
#
#  def __init__( self, syntax : str ):
#    #todo: end point is not always present, i think it just means it's continuing. needs more investigation
#    cubic_re = re.compile( f'\!{ FlaPoint.point_regex } { FlaPoint.point_regex }\((.*)\)({ FlaPoint.point_regex },{ FlaPoint.point_regex };)?')
#
#    cubic_match = re.search( cubic_re, syntax )
#    if cubic_match is not None:
#      self.start = FlaPoint( cubic_match.group(1), cubic_match.group(5) )
#      self.end   = FlaPoint( cubic_match.group(10), cubic_match.group(14) )
#
#      cubics_desc = cubic_match.group(9)
#
#      # the cubics describe four control points for the two endpoints
#      # this is followed by a list of points from the edge description that this single cubic curve is intended to replace
#      cubics_re    = re.compile( f'{ FlaPoint.point_regex },{ FlaPoint.point_regex };{ FlaPoint.point_regex },{ FlaPoint.point_regex } { FlaPoint.point_regex },{ FlaPoint.point_regex } { FlaPoint.point_regex },{ FlaPoint.point_regex }(.*)' )
#      cubics_match = re.search( cubics_re, cubics_desc )
#      if cubics_match is not None:
#        self.start_control_point_a = FlaPoint( cubics_match.group(1), cubics_match.group(5))
#        self.start_control_point_b = FlaPoint( cubics_match.group(9), cubics_match.group(13))
#        self.end_control_point_a   = FlaPoint( cubics_match.group(17), cubics_match.group(21))
#        self.end_control_point_b   = FlaPoint( cubics_match.group(25), cubics_match.group(29))
#
#        replacement_list = cubics_match.group(9)
#
#        repl_edges = [ repl_edge for repl_edge in replacement_list.split( 'q' ) if len(repl_edge) > 0 ]
#
#        self.replacements : List[ FlaEdgeCubicDescription.Replacement ] = []
#        for i_repl in range(0, len(repl_edges) - 1 ):
#          self.replacements.append( FlaEdgeCubicDescription.Replacement( repl_edges[ i_repl ], repl_edges[ i_repl + 1 ] ) )
#      else:
#        raise Exception( f'Unrecognized cubics description syntax: {cubics_desc}' )
#    else:
#      pdb.set_trace()
#      raise Exception( f'Unrecognized cubic description syntax: {syntax}' )

#------------------------------------------------------------------------------------------------
def ReadFlaEdges( shape_et : ET, ns : str ) -> List[ FlaEdge ]:
  fla_edges : List[ FlaEdge ] = []

  edges : ET = shape_et.find( f'{{{ns}}}edges' )
  if edges is not None:

    # lookup from edge id to edge description
    edge_descs   : List[ FlaEdgeDescription      ] = []

    for edge in edges.findall( f'{{{ns}}}Edge' ):
      if 'edges' in edge.attrib:
        fill_style_idx   : int = int(edge.attrib['fillStyle1'])  if 'fillStyle1'  in edge.attrib else -1
        stroke_style_idx : int = int(edge.attrib['strokeStyle']) if 'strokeStyle' in edge.attrib else -1

        edge_desc_syntaxes = edge.attrib['edges'].split('!')
        edge_descs.extend( [ FlaEdgeDescription( e, fill_style_idx, stroke_style_idx ) for e in edge_desc_syntaxes if len(e) > 0 ] )
      #elif 'cubics' in edge.attrib:
      #  cubics_descs.append( FlaEdgeCubicDescription( edge.attrib[ 'cubics' ] ) )

    # now that we have all the data to create our edges, lets do it
    while len( edge_descs ) > 0:
      #matching_cubic = None
      #for cubic in cubics_descs:
      #  if len( cubic.replacements ) > 0 and len( edge_descs ) >= len( cubic.replacements ):
      #    edge_ids   = [ edge.id for edge in edge_descs[ 0 : len(cubic.replacements) ] ]
      #    cubics_ids = [ replacement.id for replacement in cubic.replacements ]
      #    if edge_ids == cubics_ids:
      #      matching_cubic = cubic
      #      break
      #if matching_cubic is None:
        edge_desc = edge_descs[0]
        if edge_desc.type == FlaEdgeDescription.Type.Straight:
          fla_edges.append( FlaStraightEdge( edge_desc.fill_style_idx, 
                                             edge_desc.stroke_style_idx, 
                                           ( edge_desc.start.x, edge_desc.start.y ),
                                           ( edge_desc.end.x,   edge_desc.end.y   ) ) )
          del edge_descs[0]
        elif edge_desc.type == FlaEdgeDescription.Type.Quadratic:
          fla_edges.append( FlaQuadraticEdge( edge_desc.fill_style_idx,
                                              edge_desc.stroke_style_idx,
                                            ( edge_desc.start.x, edge_desc.start.y ),
                                            ( edge_desc.end.x,   edge_desc.end.y ),
                                            ( edge_desc.control_point.x, edge_desc.control_point.y ) ) )
          del edge_descs[0]
        else:
          raise Exception( f'No cubics found for b-spline edge: { edge_desc.id }' )
      #else:
      #  edge_desc = edge_descs[0]
      #  edge_descs = edge_descs[ len( cubic.replacements ) : -1 ]
      #  fla_edges.append( FlaCubicEdge( edge_desc.fill_style_idx,
      #                                  edge_desc.stroke_style_idx,
      #                                ( matching_cubic.start.x, matching_cubic.start.y ),
      #                                ( matching_cubic.end.x,   matching_cubic.end.y   ),
      #                                ( matching_cubic.start_control_point_a.x, matching_cubic.start_control_point_a.y ),
      #                                ( matching_cubic.start_control_point_b.x, matching_cubic.start_control_point_b.y ),
      #                                ( matching_cubic.end_control_point_a.x,   matching_cubic.end_control_point_a.y ),
      #                                ( matching_cubic.end_control_point_b.x,   matching_cubic.end_control_point_b.y ) ) )

  return fla_edges