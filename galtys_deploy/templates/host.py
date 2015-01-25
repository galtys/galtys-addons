def host_explore(host_id):
    import psutil
    ret=psutil.phymem_usage()
    val={'memory_total':int(ret.total)/resource.getpagesize(),
         'memory_pagesize': int( resource.getpagesize()  )}
    write('deploy.host',host_id, val )
    return val
