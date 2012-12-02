# -*- coding: utf-8 -*-
__author__ = 'nickl-'
__all__ = ('Gem', )



from .base import BaseAdapter
from aero.__version__ import __version__


class Gem(BaseAdapter):
    """
    Ruby gems adapter.
    """
    adapter_command = 'gem'

    def search(self, query):
        response = self._execute_command(self.adapter_command, ['search', '-qbd', query])[0]
        from re import match
        lst = {}
        desc = False
        blank = False
        for line in [l for l in response.splitlines() if not match('\*\*\*',l)]:
            if not desc and match('(.*)\((.*)\)', line):
                key, val = match('(.*)\((.*)\)', line).groups()
                lst[self.adapter_command + ':' + key] = 'Version: ' + val + '\n'
                desc = True
            elif desc and not blank and not line:
                blank = True
            elif desc and 'Homepage:' in line:
                lst[self.adapter_command + ':' + key] += line.replace('Homepage: ', '').strip() + '\n'
            elif desc and blank and line:
                lst[self.adapter_command + ':' + key] += line.strip() + ' '
            elif desc and blank and not line:
                desc = False
                blank = False
        return lst

    def install(self, query):
        self._execute_shell(self.adapter_command, ['install', query]).wait()
        return {}

    def info(self, query):

        import yaml

        class Timestamp(yaml.YAMLObject):

            yaml_tag = u'!timestamp'

            def __init__(self, at):
                pass #self.at = at

        class Version(yaml.YAMLObject, dict):

            yaml_tag = '!ruby/object:Gem::Version'

            def __setstate__(self, state):
                self['version'] = state['version']


        class Requirement(yaml.YAMLObject, dict):

            yaml_tag = '!ruby/object:Gem::Requirement'

            def __setstate__(self, state):
                r = state['requirements'].pop()
                self['requirement'] = '{} {}'.format(r.pop(0), r.pop(0)['version'])


        class Dependency(yaml.YAMLObject, dict):

            yaml_tag = '!ruby/object:Gem::Dependency'

            def __setstate__(self, state):
                for require in [r for r in state.keys() if 'require' in r]:
                    try:
                        self['requirement'] = state[require]['requirement']
                        break
                    except KeyError:
                        continue
                self['name'] = state['name']
                self['type'] = state['type']


        class GemSpec(yaml.YAMLObject, dict):

            yaml_tag = '!ruby/object:Gem::Specification'

            def __setstate__(self, state):
                import datetime
                for k, v in [st for st in state.items() if st[1]]:
                    if isinstance(v, list):
                        if k == 'dependencies':
                            s = []
                            mx = 0
                            for dep in v:
                                mx = max(len(dep['name']), mx)
                                s.append((dep['name'], dep['type'], dep['requirement']))
                            mx += 1
                            s = '\n'.join(['{:{}}{:12} {:12}'.format(t[0], mx, t[1], t[2]) for t in s])
                            v = s
                        else:
                            v = ', '.join(v)
                    if isinstance(v, datetime.datetime):
                        v = '{:%Y-%m-%d}'.format(v)
                    if isinstance(v, Version):
                        v = v['version']
                    if isinstance(v, Requirement):
                        v = v['requirement']
                    if not isinstance(v, str):
                        v = str(v)

                    self.update([(k, v)])

        try:
            response = self._execute_command(
                self.adapter_command, ['specification', '-qb', '--yaml', query]
            )[0]
            if 'ERROR:' in response:
                return [response]
#            f = open('/Users/inspirex/code/respect/aero/scratch/rubyforge.yaml', 'r')
#            response = ''.join(f.readlines())
#            f.close()
            result = yaml.load(sub(r'!binary', r'!!binary', response))
            return sorted(result.items())

        except BaseException as b:
            return [['Aborted: No info available for a gem called {}\nWith message: {}\n'.format(query, b)]]
