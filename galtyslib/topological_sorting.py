"""
L Empty list that will contain the sorted nodes
while there are unmarked nodes do
    select an unmarked node n
    visit(n) 
function visit(node n)
    if n has a temporary mark then stop (not a DAG)
    if n is not marked (i.e. has not been visited yet) then
        mark n temporarily
        for each node m with an edge from n to m do
            visit(m)
        mark n permanently
        add n to L

"""

def topological_sorting(dep):
    marked=[]
    temporary=[]
    L=[]

    def visit(dep, n):
        if n in temporary:
            raise ValueError
        if n not in marked:
            temporary.append(n)
            for m in dep.get(n,[]):
                visit(dep, m)
            t=temporary.index(n)
            temporary.pop(t)
            marked.append(n)
            L.append(n)
    nodes=dep.keys()
    while nodes:
        n=nodes.pop(0)
        visit(dep, n)

    return L

if __name__ == '__main__':
    dep={
        7:[11,8],
        5:[11],
        3:[8,10],
        11:[2,9],
        8:[9]}
    print topological_sorting(dep)
