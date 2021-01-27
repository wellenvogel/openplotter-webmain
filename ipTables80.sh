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
old=`iptables -L PREROUTING -n -t nat --line-numbers | grep "dpt:80  *redir  *ports  *$port" | sed 's/ .*//'`
if [ "$old" = "" ] ; then
  if [ $enable = enable ] ; then
    echo "enabling forward from port 80 to $port"
    iptables -t nat -I PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports "$port" || err "iptables insert failed"
    echo "forwarding to port $port added"
  fi
else
  if [ $enable != enable ] ; then
    iptables -t nat -D PREROUTING "$old" || err "deleting forward from iptables failed"
    echo "forwarding to port $port removed"
  fi
fi
exit 0
