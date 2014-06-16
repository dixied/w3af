"""
urlparts_mutant.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import urllib
import copy

from w3af.core.data.fuzzer.mutants.mutant import Mutant
from w3af.core.data.dc.generic.nr_kv_container import NonRepeatKeyValueContainer


TOKEN = 'token'


class URLPartsContainer(NonRepeatKeyValueContainer):
    def __init__(self, url_start, url_token, url_end):
        super(URLPartsContainer, self).__init__(init_val=[(TOKEN, url_token)])
        self.url_start = url_start
        self.url_end = url_end

        self.set_token(TOKEN)


class URLPartsMutant(Mutant):
    """
    This class is a urlparts mutant.
    """
    def __init__(self, freq):
        Mutant.__init__(self, freq)

        self._double_encoding = False
        self._safe_encode_chars = ''
        self._url_parts_dc = URLPartsContainer(None, '', None)

    def get_dc(self):
        return self._url_parts_dc

    def set_dc(self, new_dc):
        self._url_parts_dc = new_dc

    def get_token(self):
        return self.get_dc().get_token()

    @staticmethod
    def get_mutant_type():
        return 'urlparts'

    def set_double_encoding(self, double_encoding):
        self._double_encoding = double_encoding

    def set_safe_encode_chars(self, safe_chars):
        """
        :param safeChars: A string with characters we don't want to URL
                         encode in the filename. Example: '/&!'
        """
        self._safe_encode_chars = safe_chars

    def get_url(self):
        """
        :return: The URL, as modified by "set_token_value()"
        """
        domain_path = self._freq.get_url().get_domain_path()

        # Please note that this double encoding is needed if we want to work
        # with mod_rewrite
        encoded = urllib.quote_plus(self._url_parts_dc[TOKEN].get_value(),
                                    self._safe_encode_chars)
        if self._double_encoding:
            encoded = urllib.quote_plus(encoded, safe=self._safe_encode_chars)

        domain_path.set_path('%s%s%s' % (self._url_parts_dc.url_start,
                                         encoded,
                                         self._url_parts_dc.url_end))
        return domain_path

    get_uri = get_url

    def print_token_value(self):
        fmt = 'The sent %s is: "%s%s%s".'
        return fmt % (self.get_mutant_type(), self._url_parts_dc.url_start,
                      self._url_parts_dc[TOKEN], self._url_parts_dc.url_end)

    def set_url(self, u):
        msg = "You can't change the value of the URL in a URLPartsMutant"\
              " instance."
        raise ValueError(msg)

    def found_at(self):
        """
        :return: A string representing WHAT was fuzzed.
        """
        fmt = '"%s", using HTTP method %s. The modified parameter was the URL'\
              ' path, with value: "%s".'

        return fmt % (self.get_url(), self.get_method(), self.get_token_value())

    @classmethod
    def create_mutants(cls, freq, mutant_str_list, fuzzable_param_list,
                       append, fuzzer_config):
        """
        This is a very important method which is called in order to create
        mutants. Usually called from fuzzer.py module.
        """
        if not fuzzer_config['fuzz_url_parts']:
            return []

        res = []
        path_sep = '/'
        path = freq.get_url().get_path()
        path_chunks = path.split(path_sep)

        for idx, p_chunk in enumerate(path_chunks):
            if not p_chunk:
                continue

            for mutant_str in mutant_str_list:
                url_start = path_sep.join(path_chunks[:idx] + [''])
                url_end = path_sep.join([''] + path_chunks[idx + 1:])
                url_token = (p_chunk if append else '') + mutant_str

                url_parts_container = URLPartsContainer(url_start, url_token,
                                                        url_end)

                freq_copy = copy.deepcopy(freq)
                m = cls(freq_copy)
                m.set_dc(url_parts_container)
                res.append(m)

                # Same URLs but with different types of encoding!
                freq_copy = copy.deepcopy(freq)
                m2 = cls(freq_copy)
                m2.set_dc(url_parts_container)
                m2.set_double_encoding(True)

                if m2.get_url() != m.get_url():
                    res.append(m2)

        return res
