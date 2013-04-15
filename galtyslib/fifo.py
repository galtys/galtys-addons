#stock_in = [(10, 10), (30,8), (50, 7), (1,15)]
#stock_out = [5,1,8,7]
#val: [[(5, 10)], [(1, 10)], [(4, 10), (4, 8)], [(7, 8)]]
stock_in = [(10,10), (15,8), (14,9)]
stock_out=[4,8,9,1,17]

stock_total=sum([x[0] for x in stock_in])
#res = stock_total - sum(stock_out)
#stock_out.append(res)


def fifo_costing(stock_in, stock_out):
    val=[]
    b=0
    while stock_out:
        b = stock_out.pop(0)
        level=[]
        while b!=0:
            a,c = stock_in.pop(0)
            if a >= b:
                level.append( (b,c) )
                stock_in.insert( 0, ((a-b), c) )
                val.append( level )
                b=0
            else:
                level.append( (a,c) )
                b= b-a
    return val
def stock_val(res):
    out=[]
    for level in res:
        out.append( sum([b*c for b,c in level]) )
    return out

print stock_val([stock_in])
res = fifo_costing(stock_in, stock_out )


print
print stock_val(res)
