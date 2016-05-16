
# -*- coding: utf-8 -*-
"""
Written by Daniel M. Aukes and CONTRIBUTORS
Email: danaukes<at>asu.edu.
Please see LICENSE for full license.
"""

#from popupcad.geometry.vertex import ShapeVertex

import numpy
import csg_shapely

class ShapeInvalid(Exception):
    pass


class NotSimple(Exception):
    pass

class GenericShapeBase(object):
    def __init__(self,exterior,interiors,construction=False,test_shapely=False):
        self.id = id(self)
        self.exterior = exterior
        self.interiors = interiors
        self.construction = construction

    def is_valid_bool(self):
        try: 
            self.is_valid()
            return True
        except:
            return False
            
    def is_valid(self):
        shapely = self.to_shapely()
        if not shapely.is_simple:
            raise(NotSimple)
        if not shapely.is_valid:
            raise(ShapeInvalid)


    def isValid(self):
        notempty = len(self.get_exterior()) > 0
        return notempty

    def copy_data(self, new_type, identical=True):
        exterior = [vertex.copy(identical) for vertex in self.get_exterior()]
        interiors = [[vertex.copy(identical) for vertex in interior]
                     for interior in self.get_interiors()]
        new = new_type(exterior, interiors, self.is_construction())
        if identical:
            new.id = self.id
        return new

    def copy(self, identical=True):
        return self.copy_data(type(self), identical)

    def upgrade(self, identical=True):
        exterior = [vertex.upgrade(identical)
                    for vertex in self.get_exterior()]
        interiors = [[vertex.upgrade(
            identical) for vertex in interior] for interior in self.get_interiors()]
        new = type(self)(exterior, interiors, self.is_construction())
        if identical:
            new.id = self.id
        return new

    def get_exterior(self):
        return self.exterior

    def get_interiors(self):
        return self.interiors

    def is_construction(self):
        try:
            return self.construction
        except AttributeError:
            self.construction = False
            return self.construction

    def set_construction(self, test):
        self.construction = test

    def exteriorpoints(self, scaling=1):
        return [vertex.getpos(scaling) for vertex in self.get_exterior()]

    def interiorpoints(self, scaling=1):
        return [[vertex.getpos(scaling) for vertex in interior]
                for interior in self.get_interiors()]

    def exteriorpoints_3d(self, z=0):
        points = numpy.array([vertex.getpos() for vertex in self.get_exterior()])
        size = list(points.shape)
        size[1]+=1
        points2 = numpy.zeros(size)        
        points2[:,:2] = points
        points2[:,2] = z
        return points2.tolist()
        
    def interiorpoints_3d(self, z=0):
        interiors2 = []
        for interior in self.get_interiors():
            points = numpy.array([vertex.getpos() for vertex in interior])
            size = list(points.shape)
            size[1]+=1
            points2 = numpy.zeros(size)        
            points2[:,:2] = points
            points2[:,2] = z
            interiors2.append(points2.tolist())            
        return interiors2

    def vertices(self):
        vertices = self.get_exterior()[:]
        [vertices.extend(interior) for interior in self.get_interiors()]
        return vertices

    def points(self, scaling=1):
        return [vertex.getpos(scaling) for vertex in self.vertices()]

    def segments_closed(self):
        points = self.get_exterior()
        segments = list(zip(points, points[1:] + points[:1]))
        for points in self.get_interiors():
            segments.extend(list(zip(points, points[1:] + points[:1])))
        return segments

    def segments_open(self):
        points = self.get_exterior()
        segments = list(zip(points[:-1], points[1:]))
        for points in self.get_interiors():
            segments.extend(list(zip(points[:-1], points[1:])))
        return segments

    def segmentpoints(self, scaling=1):
        segments = self.segments()
        segmentpoints = [
            (point1.getpos(scaling),
             point2.getpos(scaling)) for point1,
            point2 in segments]
        return segmentpoints


    def addvertex_exterior(self, vertex, special=False):
        self.exterior.append(vertex)
        self.update_handles()

    def addvertex_exterior_special(self, vertex, special=False):
        if len(self.get_exterior()) > 2:
            if special:
                a = [v.getpos() for v in self.get_exterior()]
                b = list(zip(a, a[1:] + a[:1]))
                c = numpy.array(b)
                d = numpy.array(vertex.getpos())
                e = c - d
                f = e.reshape(-1, 4)
                g = (f**2).sum(1)
                h = g.argmin()
                self.insert_exterior_vertex(h + 1, vertex)
                self.update_handles()
                return
        self.append_exterior_vertex(vertex)
        self.update_handles()


    def removevertex(self, vertex):
        if vertex in self.exterior:
            ii = self.exterior.index(vertex)
            self.exterior.pop(ii)
        for interior in self.interiors:
            if vertex in self.interior:
                ii = interior.index(vertex)
                interior.pop(ii)
        self.update_handles()

    @staticmethod
    def _condition_loop(loop,round_vertices = False, test_rounded_vertices = True, remove_forward_redundancy=True, remove_loop_reduncancy=True,terminate_with_start = False,decimal_places = None):
        if len(loop)>0:
            if remove_forward_redundancy:
                new_loop = [loop.pop(0)]
                while not not loop:
                    v1 = new_loop[-1]
                    v2 = loop.pop(0)
                    
                    if test_rounded_vertices:
                        equal = v1.rounded_is_equal(v2,decimal_places)
                    else:
                        equal = v1.identical(v2)
                    
                    if not equal:
                        new_loop.append(v2)
            else:
                new_loop = loop[:]
            
            v1 = new_loop[0]
            v2 = new_loop[-1]
            
            if test_rounded_vertices:
                equal = v1.rounded_is_equal(v2,decimal_places)
            else:
                equal = v1.identical(v2)
            
            if terminate_with_start:
                if not equal:
                    new_loop.append(v1.copy(identical=False))       
    
            if remove_loop_reduncancy:
                if equal:
                    new_loop.pop(-1)
            
            if round_vertices:
                new_loop = [item.round(decimal_places) for item in new_loop]
            return new_loop
        else:
            return loop

    def _condition(self,round_vertices = False, test_rounded_vertices = True, remove_forward_redundancy=True, remove_loop_reduncancy=True,terminate_with_start = False,decimal_places = None):
        self.exterior = self._condition_loop(self.exterior,round_vertices = False, test_rounded_vertices = True, remove_forward_redundancy=True, remove_loop_reduncancy=True,terminate_with_start = False,decimal_places = None)
        self.interiors = [self._condition_loop(interior,round_vertices = False, test_rounded_vertices = True, remove_forward_redundancy=True, remove_loop_reduncancy=True,terminate_with_start = False,decimal_places = None) for interior in self.interiors]

    @classmethod    
    def condition_loop(cls,loop):
        return cls._condition_loop(loop)

#    def condition(self):
#        self.exterior = self.condition_loop(self.exterior)
#        self.interiors = [self.condition_loop(interior) for interior in self.interiors]
                
    def genInteractiveVertices(self):
        try:
            return self._exteriorhandles, self._interiorhandles
        except AttributeError:
            self.update_handles()
            return self._exteriorhandles, self._interiorhandles

    def update_handles(self):
        try:
            for handle in self._handles:
                handle.harddelete()
        except AttributeError:
            pass

        exterior = [vertex.gen_interactive() for vertex in self.get_exterior()]
        interiors = [[vertex.gen_interactive() for vertex in interior] for interior in self.get_interiors()]

        handles = exterior[:]
        [handles.extend(interior) for interior in interiors]
        self._exteriorhandles = exterior
        self._interiorhandles = interiors
        self._handles = handles

    def len_exterior(self):
        return len(self.get_exterior())

    def get_handles(self):
        try:
            return self._handles
        except AttributeError:
            self.update_handles()
            return self._handles

    def get_exterior_handles(self):
        try:
            return self._exteriorhandles
        except AttributeError:
            self.update_handles()
            return self._exteriorhandles

    def triangles3(self):
        return []

    @staticmethod
    def generateQPolygon(points):
        poly = qg.QPolygonF([qc.QPointF(*(point))
                             for point in numpy.array(points)])
        return poly

    def scale(self, m):
        [item.scale(m) for item in self.get_exterior()]
        [item.scale(m) for interior in self.get_interiors() for item in interior]

    def shift(self, dxdy):
        [item.shift(dxdy) for item in self.get_exterior()]
        [item.shift(dxdy) for interior in self.get_interiors()
         for item in interior]

    def transform(self, T):
        exteriorpoints = (T.dot(numpy.array(self.exteriorpoints_3d(z=1)).T)).T[:,:2].tolist()
        interiorpoints = [(T.dot(numpy.array(interior).T)).T[:,:2].tolist() for interior in self.interiorpoints_3d(z=1)]
        return self.gen_from_point_lists(exteriorpoints,interiorpoints)

    def constrained_shift(self, dxdy, constraintsystem):
        a = [(item, dxdy) for item in self.get_exterior()]
        a.extend([(item, dxdy) for interior in self.get_interiors() for item in interior])
        constraintsystem.constrained_shift(a)

    def flip(self):
        self.exterior = self.get_exterior()[::-1]
        self.interiors = [interior[::-1] for interior in self.get_interiors()]

    def hollow(self):
        return [self]

    def fill(self):
        return [self]

    def insert_exterior_vertex(self, ii, vertex):
        self.exterior.insert(ii, vertex)

    def append_exterior_vertex(self, vertex):
        self.exterior.append(vertex)

    def output_dxf(self,model_space,layer = None):
        csg = self.to_shapely()
        new = csg_shapely.to_generic(csg)
        return new.output_dxf(model_space,layer)

    def __lt__(self,other):
        return self.exteriorpoints()[0]<other.exteriorpoints()[0]

