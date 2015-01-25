#!/bin/bash
echo "sysctl"
sysctl -p /etc/sysctl.d/40-pg_buffers.conf
