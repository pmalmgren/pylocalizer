# pylocalizer
A set of Python scripts to help deal with the complexities of managing localization in Xcode

## Note
At the moment, these scripts are very much a work in progress! And please, make sure you have your Xcode project under source control, as the `--set` command will modify files inside of it directly.

## Installation

### Pre-requisites

Make sure you have a valid Google cloud account somewhere if you want to use the `--set` functionality. Also, make sure you have virtualenv installed and it is up to date.

### Commands

    $ git clone 
    $ virtualenv --prompt="(pytranslate)" --python=python3 ve
    $ pip install -r requirements.txt

## Usage

### Inspecting a project

This command will get the key for all languages in an Xcode project:

    (pytranslate) $ python add_localized_string.py [path to Xcode project] --get MyKey 

This command will translate the key for all languages in an Xcode project:
    (pytranslate) $ python add_localized_string.py [path to Xcode project] --set MyKey="My value"
    
## Future

I am trying to restructure/refactor this project into three command line tools. One will translate values (lproj_translate), one will inspect an Xcode project (lproj_inspect), and one will manipulate the values inside of the project (lproj_manipulate).
