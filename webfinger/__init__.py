from django.http import HttpResponse
import re

endpoint_hander = None

ACCT_RE = re.compile(r'(?:acct:)?(?P<local>[\w.!#$%&\'*+-/=?^_`{|}~]+)@(?P<host>[\w.:-]+)')

def _force_list(v):
    if v is not None:
        if isinstance(v, basestring):
            return [v]
        return v

class Acct(object):
    def __init__(self, acct):
        m = ACCT_RE.match(s)
        if not m:
            raise ValueError('invalid acct format')
        (local, host) = m.groups()
        self.local = local
        self.host = host
    def __unicode__(self):
        return u"acct:%s@%s" % (self.local, self.host)

class XRDResponse(HttpResponse):

    def __init__(self, subject=None, **kwargs):
        from django.conf import settings
        content_type = 'text/plain' if settings.DEBUG else 'application/xrd+xml'
        super(XRDResponse, self).__init__(content_type=content_type, **kwargs)
        self._xrd = {
            'subject': subject,
            'links': [],
            'aliases': [],
            'types': [],
        }

    def add_alias(self, alias):
        self._xrd['aliases'].append(alias)
        return self
    
    def add_type(self, type_):    
        self._xrd['types'].append(type_)
        return self
    
    def set_expires(self, expires):
        self._xrd['expires'] = expires.isoformat()
        return self

    def add_link(self, rels, uri=None, uri_template=None, media_type=None, titles=None):
            
        link = {
            'media_type': media_type,
            'rels': _force_list(rels),
            'titles': _force_list(titles),
        }
        
        if uri:
            link['uri'] = uri
        elif uri_template:
            link['uri_template'] = uri_template
        else:
            raise ValueError('one of uri or uri_template is required')
            
        self._xrd['links'].append(link)

    def __iter__(self):
        content = render_to_string('webfinger/xrd.xml', self._xrd)
        self._iterator = iter((content),)
        return self

def init():
    
    from django.core.urlresolvers import reverse
    from django.contrib.sites.models import Site
    from webfinger.rel import DESCRIBEDBY, WEBFINGER
    import wellknown
    
    endpoint = reverse('webfinger_endpoint', args=('__var__',)).replace('__var__', '{uri}')
    uri_template = "http://%s%s" % (Site.objects.get_current().domain, endpoint)

    wellknown.hostmeta.register_link(
        rels=(DESCRIBEDBY, WEBFINGER),
        uri_template=uri_template,
        title='Resource Descriptor',
    )