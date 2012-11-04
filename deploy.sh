#!/bin/bash

cp templates/page.html templates/page-backup.html
sed -i "s/REVINFO/Revision `git rev-parse --short HEAD`/g" templates/page.html

appcfg.py update .

mv templates/page-backup.html templates/page.html
