def host_explore(host_ids):
    import psutil
    ret=psutil.phymem_usage()
    write('deploy.host',host_ids, {'memory_total':int(ret.total)/resource.getpagesize() } )
    return
