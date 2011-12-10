def isFacePoint(point):
    return sum([w % 1.0 == 0 for w in point]) == 2

def isEdgePoint(point):
    return sum([w % 1.0 == 0 for w in point]) == 1

class EulerianPath(object):
    def __init__(self, graph):
        self.graph = graph
    
    def solve(self, starting = None):
        if not starting:
            starting = self.graph.edges.keys()[0]
        
        graph = self.graph.makeCopy()
        
        """
        Get initial path
        """
        def makeSimplePath(starting):
            path = [starting]
            previous = None
            current = starting
            first = True
            while first or current != starting:
                candidates = list(graph.verticesFrom(current))
                
                if first or len(candidates) == 1 or isEdgePoint(current):
                    next = candidates[0]
                else:
                    x1, y1, z1 = previous
                    x2, y2, z2 = current
                    x = 2*x2 - x1
                    if x % 1.0 == 0:
                        x = int(x)
                    y = 2*y2 - y1
                    if y % 1.0 == 0:
                        y = int(y)
                    z = 2*z2 - z1
                    if z % 1.0 == 0:
                        z = int(z)
                    next = (x, y, z)
                    assert next in candidates
                
                path.append(next)
                graph.delEdge(current, next)
                previous = current
                current = next
                first = False
            return path
        
        path = makeSimplePath(starting)
        
        i = 0
        while i < len(path) and graph.hasEdges():
            if graph.verticesFrom(path[i]):
                newPath = makeSimplePath(path[i])
                path = path[:i] + newPath + path[i + 1:]
            i += 1
        
        return path

class Graph(object):
    def __init__(self):
        self.edges = {}
    
    def hasEdges(self):
        return len(self.edges) > 0

    def addEdge(self, v1, v2):
        if v1 not in self.edges:
            self.edges[v1] = set()
        self.edges[v1].add(v2)
        if v2 not in self.edges:
            self.edges[v2] = set()
        self.edges[v2].add(v1)
        
    def delEdge(self, v1, v2):
        if v1 in self.edges and v2 in self.edges:
            self.edges[v1].remove(v2)
            if not self.edges[v1]:
                del self.edges[v1]
            self.edges[v2].remove(v1)
            if not self.edges[v2]:
                del self.edges[v2]
                
    def verticesFrom(self, v):
        if v in self.edges:
            return set(self.edges[v])
        else:
            return set()
    
    def makeCopy(self):
        copy = Graph()
        for v, e in self.edges.items():
            copy.edges[v] = set(e)
        return copy