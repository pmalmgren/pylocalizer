===========
pylocalizer
===========

A set of Python scripts to help deal with the complexities of managing localization in Xcode

Note
----
At the moment, these scripts are very much a work in progress! And please, make sure you have your Xcode project under source control, as the `--set` command will modify files inside of it directly.

Installation
------------

Pre-requisites
~~~~~~~~~~~~~~

Make sure you have a valid Google cloud account somewhere if you want to use the `--set` functionality. Also, make sure you have virtualenv installed and it is up to date.

Commands
~~~~~~~~

.. code:: bash

    $ git clone https://github.com/pmalmgren/pylocalizer.git
    $ cd pylocalizer
    $ virtualenv --prompt="(pylocalizer)" --python=python3 ve
    $ . ve/bin/activate
    $ pip install -r requirements.txt

Usage
-----

Inspecting a project
~~~~~~~~~~~~~~~~~~~~

This command will get the key for all languages in an Xcode project:

.. code:: bash

    (pylocalizer) $ python pylocalizer/add_localized_string.py [path to Xcode project] --get MyKey 

This command will translate the key for all languages in an Xcode project:

.. code:: bash

    (pylocalizer) $ python pylocalizer/add_localized_string.py [path to Xcode project] --set MyKey="My value"
