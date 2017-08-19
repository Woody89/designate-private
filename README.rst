=============
code call flow base on HF design
=============

./doc/HFdesignForDev/designate flow.png

[Flow](http://192.168.104.219/adtec/designate/blob/master/doc/HFdesignForDev/designate%20flow.png?raw=true)

===========
enable pool
===========
use /etc/designate/pools.yaml.hf to replace your env's /etc/designate/pools.yaml, keep the name as 'pools.yaml',  then run "designate-manage pool update" to update pool info in DB

get poo_id for zdns cms via access designate database: 
    select * from pools;
    
next time pls use below coomand to create zone:

     openstack  zone create --email yudzh@adtec.com.cn ccdex.com. --attributes "pool_id":"your pool id for zdns cms"


edit /etc/designate/designate.conf:

change central scheduler filters to pool_id_attribue in [service:central] section as below: 

    scheduler_filters = pool_id_attribute

Add zdns backend in /usr/lib/python2.7/site-packages/designate-4.0.0-py2.7.egg-info/entry_points.txt at  [designate.backend] section:
like below:

   zdns = designate.backend.impl_zdns:CMSBackend


disable and stop your designate-mdns, designate-producer service as below:

   systemctl disable designate-mdns designate-producer
   
   systemctl stop designate-mdns designate-producer
