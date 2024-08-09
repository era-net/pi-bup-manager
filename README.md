# Pi Backup Manager
A CLI to recursively back up your pi 🎉!


## Configuration
Configure a `config.ini` file so you don't get prompted every time you wish to create a backup.

> **Note**: The file needs to be named `config.ini`


### File content examples
`config.ini`
```ini
[RPI 4]
hostname = <your rpi ip address>
username = <your rpi username>
password = <your rpi password>
remote_path = /home/pi # detault

[RPI 3]
hostname = <rpi ip address>
username = <rpi username>
password = getpass # to be prompted
remote_path = /home/pi/Documents
```


You can set the `password` to `getpass` if you wish to be prompted in CLI.
```ini
password = getpass
```


You can leave out the `remote_path` definition if you wish to mirror the tree at `/home/pi`. So the following example would work just fine:
```ini
[RPI 3]
hostname = <rpi ip address>
username = <rpi username>
password = <rpi password>
```

Enough instructions now. Let's get to coding 🎊

. . .  to be continued  . . .