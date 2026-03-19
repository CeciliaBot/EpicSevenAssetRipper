import configparser
import os
PREFERENCES_INI_PATH = os.path.join(os.getcwd(), 'settings.ini')

config = configparser.ConfigParser()
config.optionxform = str # Preserve casing
config.read(PREFERENCES_INI_PATH)

def _setter(section: str, option: str, value: str):
    if section != 'DEFAULT':
        if not config.has_section(section):
            config.add_section(section)

    config.set(section=section, option=option, value=str(value))
    writeSettings()

def writeSettings():
    with open(PREFERENCES_INI_PATH, 'w') as f:
        config.write(f)






def getLanguage(fallback = None):
    return config.get( 'DEFAULT', 'Language', fallback=fallback if fallback else 'en')

def setLanguage(value: str):
    _setter( 'DEFAULT',  'Language', value)



def getStopOnClose():
    return config.getint( 'GUI', 'QuitRunningProcesses', fallback=0 ) != 0

def setStopOnClose(value: bool):
    _setter( 'GUI',  'QuitRunningProcesses', 0 if value == False else 1)



def getTheme():
    return config.get( 'GUI', 'Theme', fallback='dark' )

def setTheme(value: str):
    _setter( 'GUI',  'Theme', value)



def getDefaultFilePromptPath():
    return config.get('DEFAULT', 'DefaultFilePromptPath', fallback='')

def setDefaultFilePromptPath(value: str):
    _setter('DEFAULT', 'DefaultFilePromptPath', value)



def getAutosaveFileTree():
    return config.getint( 'DEFAULT', 'AutosaveFileTree', fallback=0 ) != 0

def setAutosaveFileTree(value: bool):
    _setter( 'DEFAULT',  'AutosaveFileTree', 0 if value == False else 1)



def getAutomaticFilePreview():
    return config.getint( 'GUI', 'AutomaticPreview', fallback=0 ) != 0

def setAutomaticFilePreview(value: bool):
    _setter( 'GUI',  'AutomaticPreview', 0 if value == False else 1)
