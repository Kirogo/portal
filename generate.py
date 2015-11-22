import os
import datetime
import subprocess
import time

from jinja2 import Environment, PackageLoader
from slugify import slugify
import yaml

class AtillaLearn:
    output_dir = 'web'
    authors_dir = 'content/authors'
    items_dirs = map(lambda d: os.path.join('content', d), ['conferences', 'talks', 'trainings'])
    templates_map = {
        'conference': 'conference.html',
        'talk': 'talk.html',
        'training': 'training.html'
    }

    def __init__(self):
        # Jinja stuff
        self.env = Environment(loader=PackageLoader('generate', 'templates'))

        # Content stuff
        self.authors = {} # nick -> infos dict
        self.items = {} # slug -> infos dict

        self.collect_authors()
        self.collect_items()

        # Nerd stuff
        self.nerd_dict = {
            'gen_time': datetime.datetime.now(),
            'git_sha1': subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                universal_newlines=True
            ).strip()
        }

        self.domain = 'http://learn.atilla.org'

    def collect_authors(self):
        for authorfile in os.listdir(self.authors_dir):
            if authorfile.endswith('.yaml'):
                with open(os.path.join(self.authors_dir, authorfile)) as f:
                    self.authors[authorfile.split('.')[0]] = yaml.load(f.read())

    def collect_items(self):
        for dir_ in self.items_dirs:
            for item_file in os.listdir(dir_):
                if item_file.endswith('.yaml'):
                    with open(os.path.join(dir_, item_file)) as f:
                        d = yaml.load(f.read())
                        self.items[slugify(item_file.split('.')[0])] = d

    def render_home(self):
        template = self.env.get_template('index.html')
        with open(os.path.join(self.output_dir, 'index.html'), 'w') as f:
            f.write(template.render(title='Atilla Learn', **self.nerd_dict))

    def render_landpage(self, type_, filename, title):
        entries = {
            k: v for k, v in self.items.items()
            if v['type'] == type_
        }
        template = self.env.get_template(filename)
        with open(os.path.join(self.output_dir, filename), 'w') as f:
            f.write(template.render(landpage_title=title, title=title, entries=entries, **self.nerd_dict))

    def render_item(self, slug, entry):
        if entry['type'] not in self.templates_map:
            raise ValueError('{} is not a valid item type.'.format(entry['type']))
        tpl = self.templates_map[entry['type']]

        authors = {
            k: v for k, v in self.authors.items()
            if k in entry['authors']
        }

        title = entry['title']
        template = self.env.get_template(tpl)
        with open(os.path.join(self.output_dir, slug + '.html'), 'w') as f:
            f.write(template.render(title=title, entry=entry, authors=authors, **self.nerd_dict))

    def render_sitemap(self):
        datestr = time.strftime('%Y-%m-%d', time.gmtime())

        pages = []
        pages.append({'url': self.domain, 'lastmod': datestr})
        pages.extend([
            {
                'url': self.domain + '/{}.html'.format(page),
                'lastmod': datestr
            }
            for page in ('conferences', 'trainings', 'talks')
        ])
        pages.extend([
            {
                'url': self.domain + '/{}.html'.format(slug),
                'lastmod': datestr
            }
            for slug in self.items
        ])
        template = self.env.get_template('sitemap.xml')
        with open(os.path.join(self.output_dir, 'sitemap.xml'), 'w') as f:
            f.write(template.render(pages=pages))


    def render(self):
        self.render_home()
        self.render_landpage('conference', 'conferences.html', 'Conférences')
        self.render_landpage('training', 'trainings.html', 'Formations')
        self.render_landpage('talk', 'talks.html', 'Talks')
        for slug, entry in self.items.items():
            self.render_item(slug, entry)
        self.render_sitemap()

if __name__ == '__main__':
    a = AtillaLearn()
    a.render()
