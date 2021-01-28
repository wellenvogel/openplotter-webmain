#! /bin/sh
if [ "$1" = "" -o "$2" = "" ] ; then
  echo "usage: $0 port enable|disable"
  exit 1
fi
port=$1
enable=disable
if [ "$2" = "enable" ] ; then
  enable=enable
fi

err(){
  echo "ERROR: $*"
  exit 1
}

#check for existance
old=`iptables -L PREROUTING -n -t nat --line-numbers | grep "dpt:80  *redir  *ports  *$port" | head -1 | sed 's/ .*//'`
oldi=`iptables -L OUTPUT -v -t nat --line-numbers -n | grep "dpt:80  *redir  *ports  *$port" | head -1 | sed 's/ .*//'`
if [ $enable = enable ] ; then
  if [ "$old" = "" ] ; then
    echo "enabling forward from port 80 to $port ext"
    iptables -t nat -I PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports "$port" || err "iptables insert failed"
    echo "forwarding to port $port added"
  fi
  if [ "$oldi" = "" ] ; then
    echo "enabling forward from port 80 to $port int"
    iptables -t nat -I OUTPUT -p tcp -o lo --dport 80 -j REDIRECT --to-ports "$port" || err "iptables insert failed"
    echo "forwarding to port $port added"
  fi  
else
  if [ "$old" != "" ] ; then
    iptables -t nat -D PREROUTING "$old" || err "deleting forward from iptables failed"
    echo "ext forwarding to port $port removed"
  fi
  if [ "$oldi" != "" ] ; then
    iptables -t nat -D OUTPUT "$oldi" || err "deleting forward from iptables failed"
    echo "int forwarding to port $port removed"
  fi
fi
exit 0
