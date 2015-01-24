def host_explore(host_ids):
    import psutil
    #print 'explore host', host_ids
    ret=psutil.phymem_usage()
    write('deploy.host',host_ids, {'memory_total':int(ret.total)/resource.getpagesize(),
                                   'memory_pagesize': int( resource.getpagesize()  )} )
    return
