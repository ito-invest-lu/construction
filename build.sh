#/bin/bash

# delete all __init__.py files as they are not required since Odoo 11.0
find . -name '__init__.py' | xargs rm -rf

cd setup

for f in ./*; do
    echo 'Deploy module' $f
    if [ -d $f ]; then
        cd $f
        echo 'Deploy module' $f
        python setup.py sdist upload -r pypi-server
        cd ..
    fi
done
