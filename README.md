ZenPack Usage
-------------
This scripts lists all the templates in the inventory of Zenoss and tries to retrieve whether they are in use and 
whether they are defined in a ZenPack. 

How to run a ZenDMD script
--------------------------
1. In a test environment, it's quite easy if you have build your environment as described here: https://help.zenoss.com/dev/zenpack-sdk/development-environment. In such case, you simply
   have to copy the script under the /z folder or any sub-folder of it and call it from the same location within the container.
2. You can copy the script in the container and run it in the container. (More details needed) 
3. You can also launch a container and mount the current folder into it. (More details needed)
4. A better solution is to copy the script under /zenoss-var-ext folder, under the DFS structure. The script is then permanently available from the zope containers under /opt/zenoss/var/ext. 
