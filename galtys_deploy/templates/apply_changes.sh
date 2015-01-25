#!/bin/bash
echo "running sysctl"
sudo sysctl -p /etc/sysctl.d/40-pg_buffers.conf
