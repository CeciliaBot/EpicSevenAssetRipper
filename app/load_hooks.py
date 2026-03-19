import importlib
import sys
import os
import re
from pathlib        import Path
from types          import ModuleType
from typing         import Literal, TYPE_CHECKING
import traceback

if TYPE_CHECKING: from app.util.misc  import FileDescriptor
else: FileDescriptor = None

TimingsType = Literal['before', 'after']

class HookClass:
    module: ModuleType = None
    _is_enabled = True
    def __init__(self, path: str = '', file_name: str = '', timing: TimingsType = 'before', module = None):
        self.path = path
        self.file_name = file_name
        self.timing = timing
        self.import_name = f'app.hooks.{self.timing}_write.{self.file_name}'

        try:
            self.module = self._load_module()
            self._is_enabled = getattr(self.module, '_IS_ENABLED_', True)
        except Exception as e:
            print(e)
            pass

    def __load_module__(self):
        spec = importlib.util.spec_from_file_location(self.import_name, os.path.join(self.path, f'{self.file_name}.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def _load_module(self, reload=False) -> ModuleType:
        python_path_style = self.import_name
        still_exists = self._exists()

        # Check for all possible conditions
        if still_exists:
            if reload:
                return self.__load_module__()
            elif python_path_style in sys.modules:
                return sys.modules[python_path_style]
            elif not self.module:
                return self.__load_module__()
            else:
                return self.module
        elif not still_exists and reload: # If a reload was requested but the file has been deleted then return null and in the reload function destroy this instance
            return None
        else:
            return self.module

    def _exists(self):
        try:
            return os.path.exists( os.path.join(self.path, self.file_name + '.py') )
        except Exception:
            return False

    def reload(self):
        self.destroy()
        self.module = self._load_module(reload=True)
        return self.module

    def get_name(self):
        try:
            name = getattr(self.module, '_ADDON_NAME_', self.file_name)
        except Exception as e:
            name = self.file_name
            print(e)
        return name
    
    def get_is_enabled(self):
        return self._is_enabled
        # try:
        #     return getattr(self.module, '_IS_ENABLED_')
        # except Exception:
        #     return True
        
    def set_is_enabled(self, value: bool):
        # return setattr(self.module, '_IS_ENABLED_', value)
        try:
            self.module.onEnabled() if value == True else self.module.onDisabled()
        except AttributeError:
            pass
        except Exception as e:
            print(e)
        return setattr(self, '_is_enabled', value)

    def get_has_icon(self):
        return getattr(self.module, '_PREVENT_DEFAULT_ICON_', False) != True

    def exec(self, *args, **kwargs):
        try:
            if self.get_is_enabled():
                self.module.main(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()

    def on_before_destroy(self):
        pass

    def destroy(self):
        self.on_before_destroy()

        try:
            # Each module can provide a custom clean up destroy method
            self.module.destroy()
        except Exception:
            pass
        finally:
            self.module = None




hooks: dict[TimingsType, dict[str, HookClass]] = {
    'before': {},
    'after': {}
}


def load_hooks(gui_create=None):
    global hooks
    cfile_path = os.path.split(__file__)[0]
    errors = 0
    success = 0

    # Create folders if missing
    Path( cfile_path, 'hooks', 'before_write').mkdir(parents=True, exist_ok=True)
    Path( cfile_path, 'hooks', 'after_write').mkdir(parents=True, exist_ok=True)

    try:
        for hook in ['before', 'after']:

            # Reload Existing hooks
            keys = list(hooks[hook])
            for h in keys:
                l = hooks[hook][h]
                l.reload()
                if l.module:
                    if gui_create:
                        gui_create(l)
                    success+=1
                else: # If after reloading the module is None then the file has been deleted
                    del hooks[hook][h]
                    l.destroy()

            hook_folder_path = os.path.join(cfile_path, 'hooks', f'{hook}_write')

            files = os.listdir(hook_folder_path)
            for file in files:
                target_extension = re.search(r"^([^ ]+)\.py$", file)
                if target_extension:
                    ext = target_extension.group(1)

                    if ext in hooks[hook]: # Module was refreshed, no need to create another instance
                        continue

                    try:
                        plugin = HookClass(file_name=ext, path=hook_folder_path, timing=hook)
                        if plugin.module is None:
                            continue
                    except Exception as e:
                        print(ext, traceback.format_exc())
                        errors+=1
                        continue

                    hooks[hook][ext] = plugin
                    if gui_create and plugin.get_has_icon():
                        gui_create(plugin)

                    success+=1

    except Exception as e:
        errors+=1
        print(e)


    return success, errors


# █████████████████████████████████████████████████
def call_hooks(timing: TimingsType, file: FileDescriptor):
    '''
        Use the hook for the file type. Timing can be "before" and "after" the writing phase
    '''
    module = hooks[timing].get(file.tree_file['format'])
    if module:
        module.exec(file)
