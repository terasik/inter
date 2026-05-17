# (c) 2014, James Tanner <tanner.jc@gmail.com>
# (c) 2016, Adrian Likins <alikins@redhat.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations


import functools
import os
import random
import sys
import warnings
import logging

from binascii import hexlify
from binascii import unhexlify
from binascii import Error as BinasciiError

HAS_CRYPTOGRAPHY = False
CRYPTOGRAPHY_BACKEND = None
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, padding
    from cryptography.hazmat.primitives.hmac import HMAC
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import (
        Cipher as C_Cipher, algorithms, modes
    )
    CRYPTOGRAPHY_BACKEND = default_backend()
    HAS_CRYPTOGRAPHY = True
except ImportError:
    pass

from .converters import to_bytes, to_text, to_native

class Display():

    def __init__(self):
        #logging.basicConfig(level=logging.INFO, 
        #                format="%(asctime)s %(levelname)s [%(module)s %(funcName)s] %(message)s")
        self.logger=logging.getLogger("ansivault")
        #self.logger.setLevel(logging.INFO)
        pass
        
    def log(self, msg):
        logging.debug(msg)

    def v(self, msg):
        self.logger.debug(msg)
      
    def vv(self, msg):
        self.logger.debug(msg)
      
    def vvv(self, msg):
        self.logger.debug(msg)

    def vvvv(self, msg):
        self.logger.debug(msg)
      
    def vvvvv(self, msg):
        self.logger.debug(msg)
      
    def vvvvvv(self, msg):
        self.logger.debug(msg)
      
    def vvvvvvv(self, msg):
        self.logger.debug(msg)
      
display = Display()


b_HEADER = b'$ANSIBLE_VAULT'
CIPHER_ALLOWLIST = frozenset((u'AES256',))
CIPHER_WRITE_ALLOWLIST = frozenset((u'AES256',))
# See also CIPHER_MAPPING at the bottom of the file which maps cipher strings
# (used in VaultFile header) to a cipher class

NEED_CRYPTO_LIBRARY = "ansible-vault requires the cryptography library in order to function"

# see site-packages/ansible/config/base.yml
DEFAULT_VAULT_ID_MATCH=os.environ.get("ANSIBLE_VAULT_ID_MATCH", False)
DEFAULT_VAULT_IDENTITY=os.environ.get("ANSIBLE_VAULT_IDENTITY", 'default')
VAULT_ENCRYPT_SALT=os.environ.get("ANSIBLE_VAULT_ENCRYPT_SALT", None)

class AnsibleError(Exception):
    pass

class AnsibleVaultError(AnsibleError):
    pass

class AnsibleVaultPasswordError(AnsibleVaultError):
    pass

class AnsibleVaultFormatError(AnsibleError):
    pass


def is_encrypted(data):
    """ Test if this is vault encrypted data blob

    :arg data: a byte or text string to test whether it is recognized as vault
        encrypted data
    :returns: True if it is recognized.  Otherwise, False.
    """
    try:
        # Make sure we have a byte string and that it only contains ascii
        # bytes.
        b_data = to_bytes(to_text(data, encoding='ascii', errors='strict', nonstring='strict'), encoding='ascii', errors='strict')
    except (UnicodeError, TypeError):
        # The vault format is pure ascii so if we failed to encode to bytes
        # via ascii we know that this is not vault data.
        # Similarly, if it's not a string, it's not vault data
        return False

    if b_data.startswith(b_HEADER):
        return True
    return False


def is_encrypted_file(file_obj, start_pos=0, count=len(b_HEADER)):
    """Test if the contents of a file obj are a vault encrypted data blob.

    :arg file_obj: A file object that will be read from.
    :kwarg start_pos: A byte offset in the file to start reading the header
        from.  Defaults to 0, the beginning of the file.
    :kwarg count: Read up to this number of bytes from the file to determine
        if it looks like encrypted vault data. The default is the size of the
        the vault header, which is what is needed most times.
        For some IO classes, or files that don't begin with the vault itself,
        set to -1 to read to the end of file.
    :returns: True if the file looks like a vault file. Otherwise, False.
    """
    # read the header and reset the file stream to where it started
    current_position = file_obj.tell()
    try:
        file_obj.seek(start_pos)
        return is_encrypted(file_obj.read(count))

    finally:
        file_obj.seek(current_position)


def _parse_vaulttext_envelope(b_vaulttext_envelope, default_vault_id=None):

    b_tmpdata = b_vaulttext_envelope.splitlines()
    b_tmpheader = b_tmpdata[0].strip().split(b';')

    b_version = b_tmpheader[1].strip()
    cipher_name = to_text(b_tmpheader[2].strip())
    vault_id = default_vault_id

    # Only attempt to find vault_id if the vault file is version 1.2 or newer
    # if self.b_version == b'1.2':
    if len(b_tmpheader) >= 4:
        vault_id = to_text(b_tmpheader[3].strip())

    b_ciphertext = b''.join(b_tmpdata[1:])
    # DTFIX7: possible candidate for propagate_origin
    #b_ciphertext = AnsibleTagHelper.tag_copy(b_vaulttext_envelope, b_ciphertext)

    return b_ciphertext, b_version, cipher_name, vault_id


def parse_vaulttext_envelope(b_vaulttext_envelope, default_vault_id=None):
    """Parse the vaulttext envelope

    When data is saved, it has a header prepended and is formatted into 80
    character lines.  This method extracts the information from the header
    and then removes the header and the inserted newlines.  The string returned
    is suitable for processing by the Cipher classes.

    :arg b_vaulttext_envelope: byte str containing the data from a save file
    :arg default_vault_id: The vault_id name to use if the vaulttext does not provide one.
    :returns: A tuple of byte str of the vaulttext suitable to pass to parse_vaultext,
        a byte str of the vault format version,
        the name of the cipher used, and the vault_id.
    :raises: AnsibleVaultFormatError: if the vaulttext_envelope format is invalid
    """
    # used by decrypt
    default_vault_id = default_vault_id or DEFAULT_VAULT_IDENTITY
    #print(f"b_vaulttext_envelope: {b_vaulttext_envelope}")

    try:
        r=_parse_vaulttext_envelope(b_vaulttext_envelope, default_vault_id)
    except Exception as ex:
        #raise AnsibleVaultFormatError("Vault envelope format error.", obj=b_vaulttext_envelope) from ex
        raise AnsibleVaultFormatError("Vault envelope format error %s" % b_vaulttext_envelope) from ex
    else:
        return r


def format_vaulttext_envelope(b_ciphertext, cipher_name, version=None, vault_id=None):
    """ Add header and format to 80 columns

        :arg b_ciphertext: the encrypted and hexlified data as a byte string
        :arg cipher_name: unicode cipher name (for ex, u'AES256')
        :arg version: unicode vault version (for ex, '1.2'). Optional ('1.1' is default)
        :arg vault_id: unicode vault identifier. If provided, the version will be bumped to 1.2.
        :returns: a byte str that should be dumped into a file.  It's
            formatted to 80 char columns and has the header prepended
    """

    if not cipher_name:
        raise AnsibleError("the cipher must be set before adding a header")

    version = version or '1.1'

    # If we specify a vault_id, use format version 1.2. For no vault_id, stick to 1.1
    if vault_id and vault_id != u'default':
        version = '1.2'

    b_version = to_bytes(version, 'utf-8', errors='strict')
    b_vault_id = to_bytes(vault_id, 'utf-8', errors='strict')
    b_cipher_name = to_bytes(cipher_name, 'utf-8', errors='strict')

    header_parts = [b_HEADER,
                    b_version,
                    b_cipher_name]

    if b_version == b'1.2' and b_vault_id:
        header_parts.append(b_vault_id)

    header = b';'.join(header_parts)

    b_vaulttext = [header]
    b_vaulttext += [b_ciphertext[i:i + 80] for i in range(0, len(b_ciphertext), 80)]
    b_vaulttext += [b'']
    b_vaulttext = b'\n'.join(b_vaulttext)

    return b_vaulttext


def _unhexlify(b_data):
    try:
        unbd=unhexlify(b_data)
        return unbd
    except (BinasciiError, TypeError) as ex:
        raise AnsibleVaultFormatError("Vault format unhexlify error %s" % b_data) from ex


def _parse_vaulttext(b_vaulttext):
    b_vaulttext = _unhexlify(b_vaulttext)
    b_salt, b_crypted_hmac, b_ciphertext = b_vaulttext.split(b"\n", 2)
    b_salt = _unhexlify(b_salt)
    b_ciphertext = _unhexlify(b_ciphertext)

    return b_ciphertext, b_salt, b_crypted_hmac


def parse_vaulttext(b_vaulttext):
    """Parse the vaulttext

    :arg b_vaulttext: byte str containing the vaulttext (ciphertext, salt, crypted_hmac)
    :returns: A tuple of byte str of the ciphertext suitable for passing to a
        Cipher class's decrypt() function, a byte str of the salt,
        and a byte str of the crypted_hmac
    :raises: AnsibleVaultFormatError: if the vaulttext format is invalid
    """
    # SPLIT SALT, DIGEST, AND DATA
    try:
        return _parse_vaulttext(b_vaulttext)
    except AnsibleVaultFormatError:
        raise
    except Exception as ex:
        raise AnsibleVaultFormatError("Vault vaulttext format error %s" % b_vaulttext) from ex


def verify_secret_is_not_empty(secret, msg=None):
    """Check the secret against minimal requirements.

    Raises: AnsibleVaultPasswordError if the password does not meet requirements.

    Currently, only requirement is that the password is not None or an empty string.
    """
    msg = msg or 'Invalid vault password was provided'
    if not secret:
        raise AnsibleVaultPasswordError(msg)


class VaultSecret:
    """Opaque/abstract objects for a single vault secret. ie, a password or a key."""

    def __init__(self, _bytes=None):
        # FIXME: ? that seems wrong... Unset etc?
        self._bytes = _bytes

    @property
    def bytes(self):
        """The secret as a bytestring.

        Sub classes that store text types will need to override to encode the text to bytes.
        """
        return self._bytes

    def load(self):
        return self._bytes


def match_secrets(secrets, target_vault_ids):
    """Find all VaultSecret objects that are mapped to any of the target_vault_ids in secrets"""
    if not secrets:
        return []

    matches = [(vault_id, secret) for vault_id, secret in secrets if vault_id in target_vault_ids]
    return matches


def match_best_secret(secrets, target_vault_ids):
    """Find the best secret from secrets that matches target_vault_ids

    Since secrets should be ordered so the early secrets are 'better' than later ones, this
    just finds all the matches, then returns the first secret"""
    matches = match_secrets(secrets, target_vault_ids)
    if matches:
        return matches[0]
    # raise exception?
    return None


def match_encrypt_vault_id_secret(secrets, encrypt_vault_id=None):
    # See if the --encrypt-vault-id matches a vault-id
    display.vvvv(u'encrypt_vault_id=%s' % to_text(encrypt_vault_id))

    if encrypt_vault_id is None:
        raise AnsibleError('match_encrypt_vault_id_secret requires a non None encrypt_vault_id')

    encrypt_vault_id_matchers = [encrypt_vault_id]
    encrypt_secret = match_best_secret(secrets, encrypt_vault_id_matchers)

    # return the best match for --encrypt-vault-id
    if encrypt_secret:
        return encrypt_secret

    # If we specified a encrypt_vault_id and we couldn't find it, dont
    # fallback to using the first/best secret
    raise AnsibleVaultError('Did not find a match for --encrypt-vault-id=%s in the known vault-ids %s' % (encrypt_vault_id,
                                                                                                          [_v for _v, _vs in secrets]))


def match_encrypt_secret(secrets, encrypt_vault_id=None):
    """Find the best/first/only secret in secrets to use for encrypting"""

    display.vvvv(u'encrypt_vault_id=%s' % to_text(encrypt_vault_id))
    # See if the --encrypt-vault-id matches a vault-id
    if encrypt_vault_id:
        return match_encrypt_vault_id_secret(secrets,
                                             encrypt_vault_id=encrypt_vault_id)

    # Find the best/first secret from secrets since we didn't specify otherwise
    # ie, consider all the available secrets as matches
    _vault_id_matchers = [_vault_id for _vault_id, dummy in secrets]
    best_secret = match_best_secret(secrets, _vault_id_matchers)

    # can be empty list sans any tuple
    return best_secret


class VaultLib:
    def __init__(self, secrets=None):
        self.secrets = secrets or []
        self.cipher_name = None
        self.b_version = b'1.2'

    @staticmethod
    def is_encrypted(vaulttext):
        return is_encrypted(vaulttext)

    def encrypt(self, plaintext, secret=None, vault_id=None, salt=None):
        """Vault encrypt a piece of data.

        :arg plaintext: a text or byte string to encrypt.
        :returns: a utf-8 encoded byte str of encrypted data.  The string
            contains a header identifying this as vault encrypted data and
            formatted to newline terminated lines of 80 characters.  This is
            suitable for dumping as is to a vault file.

        If the string passed in is a text string, it will be encoded to UTF-8
        before encryption.
        """

        if secret is None:
            if self.secrets:
                dummy, secret = match_encrypt_secret(self.secrets)
            else:
                raise AnsibleVaultError("A vault password must be specified to encrypt data")

        b_plaintext = to_bytes(plaintext, errors='surrogate_or_strict')

        if is_encrypted(b_plaintext):
            raise AnsibleError("input is already encrypted")

        if not self.cipher_name or self.cipher_name not in CIPHER_WRITE_ALLOWLIST:
            self.cipher_name = u"AES256"

        try:
            this_cipher = CIPHER_MAPPING[self.cipher_name]()
        except KeyError:
            raise AnsibleError(u"{0} cipher could not be found".format(self.cipher_name))

        # encrypt data
        if vault_id:
            display.vvvvv(u'Encrypting with vault_id "%s" and vault secret %s' % (to_text(vault_id), to_text(secret)))
        else:
            display.vvvvv(u'Encrypting without a vault_id using vault secret %s' % to_text(secret))

        b_ciphertext = this_cipher.encrypt(b_plaintext, secret, salt)

        # format the data for output to the file
        b_vaulttext = format_vaulttext_envelope(b_ciphertext,
                                                self.cipher_name,
                                                vault_id=vault_id)
        return b_vaulttext

    def decrypt(self, vaulttext):
        """Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :returns: a byte string containing the decrypted data
        """
        plaintext, vault_id, vault_secret = self.decrypt_and_get_vault_id(vaulttext)
        return plaintext

    def decrypt_and_get_vault_id(self, vaulttext):
        """Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :returns: a byte string containing the decrypted data and the vault-id vault-secret that was used
        """
        #origin = Origin.get_tag(vaulttext)

        b_vaulttext = to_bytes(vaulttext, nonstring='error')  # enforce vaulttext is str/bytes, keep type check if removing type conversion

        if self.secrets is None:
            raise AnsibleVaultError("A vault password must be specified to decrypt data %s" % vaulttext)

        if not is_encrypted(b_vaulttext):
            raise AnsibleVaultError("Input is not vault encrypted data %s" % vaulttext)

        b_vaulttext, dummy, cipher_name, vault_id = parse_vaulttext_envelope(b_vaulttext)

        # create the cipher object, note that the cipher used for decrypt can
        # be different than the cipher used for encrypt
        if cipher_name in CIPHER_ALLOWLIST:
            this_cipher = CIPHER_MAPPING[cipher_name]()
        else:
            raise AnsibleVaultError(f"Cipher {cipher_name!r} could not be found %s" % vaulttext)

        if not self.secrets:
            raise AnsibleVaultError("Attempting to decrypt but no vault secrets found %s" % vaulttext)

        # WARNING: Currently, the vault id is not required to match the vault id in the vault blob to
        #          decrypt a vault properly. The vault id in the vault blob is not part of the encrypted
        #          or signed vault payload. There is no cryptographic checking/verification/validation of the
        #          vault blobs vault id. It can be tampered with and changed. The vault id is just a nick
        #          name to use to pick the best secret and provide some ux/ui info.

        # iterate over all the applicable secrets (all of them by default) until one works...
        # if we specify a vault_id, only the corresponding vault secret is checked and
        # we check it first.

        vault_id_matchers = []

        if vault_id:
            display.vvvvv(u'Found a vault_id (%s) in the vaulttext' % to_text(vault_id))
            vault_id_matchers.append(vault_id)
            _matches = match_secrets(self.secrets, vault_id_matchers)
            if _matches:
                display.vvvvv(u'We have a secret associated with vault id (%s), will try to use to decrypt' % (to_text(vault_id)))
            else:
                display.vvvvv(u'Found a vault_id (%s) in the vault text, but we do not have a associated secret (--vault-id)' % to_text(vault_id))

        # Not adding the other secrets to vault_secret_ids enforces a match between the vault_id from the vault_text and
        # the known vault secrets.
        if not DEFAULT_VAULT_ID_MATCH:
            # Add all of the known vault_ids as candidates for decrypting a vault.
            vault_id_matchers.extend([_vault_id for _vault_id, _dummy in self.secrets if _vault_id != vault_id])

        matched_secrets = match_secrets(self.secrets, vault_id_matchers)

        # for vault_secret_id in vault_secret_ids:
        for vault_secret_id, vault_secret in matched_secrets:
            display.vvvvv(u'Trying to use vault secret=(%s) id=%s to decrypt' % (to_text(vault_secret), to_text(vault_secret_id)))

            try:
                # secret = self.secrets[vault_secret_id]
                display.vvvv(u'Trying secret %s for vault_id=%s' % (to_text(vault_secret), to_text(vault_secret_id)))
                b_plaintext = this_cipher.decrypt(b_vaulttext, vault_secret)
                # DTFIX7: possible candidate for propagate_origin
                #b_plaintext = AnsibleTagHelper.tag_copy(vaulttext, b_plaintext)
                if b_plaintext is not None:
                    vault_id_used = vault_secret_id
                    vault_secret_used = vault_secret
                    file_slug = ''
                    #if origin:
                    #    file_slug = ' of "%s"' % origin
                    display.vvvvv(
                        u'Decrypt successful with secret=%s and vault_id=%s' % (to_text(vault_secret), to_text(vault_secret_id))
                    )
                    break
            except AnsibleVaultFormatError:
                raise
            except AnsibleError as e:
                display.vvvv(u'Tried to use the vault secret (%s) to decrypt but it failed. Error: %s' %
                             (to_text(vault_secret_id), e))
                continue
        else:
            raise AnsibleVaultError("Decryption failed (no vault secrets were found that could decrypt) %s" % vaulttext)

        return b_plaintext, vault_id_used, vault_secret_used



########################################
#               CIPHERS                #
########################################

class VaultAES256:

    """
    Vault implementation using AES-CTR with an HMAC-SHA256 authentication code.
    Keys are derived using PBKDF2
    """

    # http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html

    # Note: strings in this class should be byte strings by default.

    def __init__(self):
        if not HAS_CRYPTOGRAPHY:
            raise AnsibleError(NEED_CRYPTO_LIBRARY)

    @staticmethod
    def _create_key_cryptography(b_password, b_salt, key_length, iv_length):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=2 * key_length + iv_length,
            salt=b_salt,
            iterations=10000,
            backend=CRYPTOGRAPHY_BACKEND)
        b_derivedkey = kdf.derive(b_password)

        return b_derivedkey

    @classmethod
    @functools.cache  # Concurrent first-use by multiple threads will all execute the method body.
    def _gen_key_initctr(cls, b_password, b_salt):
        # 16 for AES 128, 32 for AES256
        key_length = 32

        if HAS_CRYPTOGRAPHY:
            # AES is a 128-bit block cipher, so IVs and counter nonces are 16 bytes
            iv_length = algorithms.AES.block_size // 8

            b_derivedkey = cls._create_key_cryptography(b_password, b_salt, key_length, iv_length)
            b_iv = b_derivedkey[(key_length * 2):(key_length * 2) + iv_length]
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in initctr)')

        b_key1 = b_derivedkey[:key_length]
        b_key2 = b_derivedkey[key_length:(key_length * 2)]

        return b_key1, b_key2, b_iv

    @staticmethod
    def _encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv):
        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        b_ciphertext = encryptor.update(padder.update(b_plaintext) + padder.finalize())
        b_ciphertext += encryptor.finalize()

        # COMBINE SALT, DIGEST AND DATA
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        b_hmac = hmac.finalize()

        return to_bytes(hexlify(b_hmac), errors='surrogate_or_strict'), hexlify(b_ciphertext)

    @classmethod
    def _get_salt(cls):
        #custom_salt = C.config.get_config_value('VAULT_ENCRYPT_SALT')
        custom_salt = VAULT_ENCRYPT_SALT
        if not custom_salt:
            custom_salt = os.urandom(32)
        return to_bytes(custom_salt)

    @classmethod
    def encrypt(cls, b_plaintext, secret, salt=None):

        if secret is None:
            raise AnsibleVaultError('The secret passed to encrypt() was None')

        if salt is None:
            b_salt = cls._get_salt()
        elif not salt:
            raise AnsibleVaultError('Empty or invalid salt passed to encrypt()')
        else:
            b_salt = to_bytes(salt)

        b_password = secret.bytes
        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        if HAS_CRYPTOGRAPHY:
            b_hmac, b_ciphertext = cls._encrypt_cryptography(b_plaintext, b_key1, b_key2, b_iv)
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in encrypt)')

        b_vaulttext = b'\n'.join([hexlify(b_salt), b_hmac, b_ciphertext])
        # Unnecessary but getting rid of it is a backwards incompatible vault
        # format change
        b_vaulttext = hexlify(b_vaulttext)
        return b_vaulttext

    @classmethod
    def _decrypt_cryptography(cls, b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv):
        # b_key1, b_key2, b_iv = self._gen_key_initctr(b_password, b_salt)
        # EXIT EARLY IF DIGEST DOESN'T MATCH
        hmac = HMAC(b_key2, hashes.SHA256(), CRYPTOGRAPHY_BACKEND)
        hmac.update(b_ciphertext)
        try:
            hmac.verify(_unhexlify(b_crypted_hmac))
        except InvalidSignature as e:
            raise AnsibleVaultError('HMAC verification failed: %s' % e)

        cipher = C_Cipher(algorithms.AES(b_key1), modes.CTR(b_iv), CRYPTOGRAPHY_BACKEND)
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        b_plaintext = unpadder.update(
            decryptor.update(b_ciphertext) + decryptor.finalize()
        ) + unpadder.finalize()

        return b_plaintext

    @staticmethod
    def _is_equal(b_a, b_b):
        """
        Comparing 2 byte arrays in constant time to avoid timing attacks.

        It would be nice if there were a library for this but hey.
        """
        if not (isinstance(b_a, binary_type) and isinstance(b_b, binary_type)):
            raise TypeError('_is_equal can only be used to compare two byte strings')

        # http://codahale.com/a-lesson-in-timing-attacks/
        if len(b_a) != len(b_b):
            return False

        result = 0
        for b_x, b_y in zip(b_a, b_b):
            result |= b_x ^ b_y
        return result == 0

    @classmethod
    def decrypt(cls, b_vaulttext, secret):

        b_ciphertext, b_salt, b_crypted_hmac = parse_vaulttext(b_vaulttext)

        # TODO: would be nice if a VaultSecret could be passed directly to _decrypt_*
        #       (move _gen_key_initctr() to a AES256 VaultSecret or VaultContext impl?)
        # though, likely needs to be python cryptography specific impl that basically
        # creates a Cipher() with b_key1, a Mode.CTR() with b_iv, and a HMAC() with sign key b_key2
        b_password = secret.bytes

        b_key1, b_key2, b_iv = cls._gen_key_initctr(b_password, b_salt)

        if HAS_CRYPTOGRAPHY:
            b_plaintext = cls._decrypt_cryptography(b_ciphertext, b_crypted_hmac, b_key1, b_key2, b_iv)
        else:
            raise AnsibleError(NEED_CRYPTO_LIBRARY + '(Detected in decrypt)')

        return b_plaintext


# Keys could be made bytes later if the code that gets the data is more
# naturally byte-oriented
CIPHER_MAPPING = {
    u'AES256': VaultAES256,
}

