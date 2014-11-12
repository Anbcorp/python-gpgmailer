#!/usr/bin/env python
"""
Send encrypted mail with proper MIME format
Supports attachements and multiple recipients (exploded as multiple
        single-recipient mails)
Based on RFC3156

Depends on python-gnupg and python-magic
"""
import gnupg
import magic
import smtplib, os
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders


class Mailer(object):

    def __init__(self, send_from,
            gpghome=os.path.join(os.environ['HOME'], '.gnupg'),
            server="localhost"):
        self.gpg = gnupg.GPG(gnupghome=gpghome)
        self.server = server
        self.send_from = send_from

    def send_mail(self, send_to, subject, text, files=[], encrypted=True):
        """
        Create and send an email, with or without attachments, that may be
        encrypted using gpg public keys of recipients (default)

        send_to and files must be lists

        If using encryption and some of the recipients public key can't be found
        in the keyring, an error message will be logged It is the responsibility
        of the user to ensure the public keys of the recipient are :
            - valid
            - trusted
            - added in the keyring
        """
        assert isinstance(send_to, list)
        assert isinstance(files, list)

        # Build standard MIME message
        msg = MIMEMultipart()
        msg.attach(MIMEText(text))

        # Attach files if any
        mime = magic.Magic(mime=True)
        for fil in files:
            # Try to autoguess the file format and mimetype
            mimetype = mime.from_file(fil)
            if mimetype.find('/') == -1:
                mimemain = 'application'
                mimesub = 'octet-stream'
            else:
                (mimemain, mimesub) = mimetype.split('/')
            part = MIMEBase(mimemain, mimesub)
            part.set_payload(open(fil, "rb").read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                    'attachment; filename="%s"' % os.path.basename(fil))
            msg.attach(part)

        # Generate encrypted message as per RFC3156
        if encrypted:
            for recipient in send_to:
                encrypted_msg = self.encrypt_mail(msg, recipient)
                if not encrypted_msg:
                    print "Error, %s public key not found in keyring" % recipient
                self.send_msg(recipient, subject, encrypted_msg)
        # Or send message unencrypted
        else:
            self.send_msg(send_to, subject, msg)


    def send_msg(self, send_to, subject, msg):
        """
        Send a message.

        Send_to can be a single recipient as string or a list of
        multiple-recipients
        """
        if not (isinstance(send_to, list) or isinstance(send_to, tuple)):
            send_to = [send_to,]

        msg['From'] = self.send_from
        msg['To'] = COMMASPACE.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        smtp = smtplib.SMTP(self.server)
        smtp.sendmail(self.send_from, send_to, msg.as_string())
        smtp.close()


    def encrypt_mail(self, raw_msg, recipient):
        """
        Encrypt raw_msg as a RFC3156 encrypted-message
        """

        encrypted_msg = self.gpg.encrypt(
            raw_msg.as_string(),
            recipient,
            always_trust=True)

        msg = MIMEMultipart('encrypted')

        head = MIMEBase('application', 'pgp-encrypted')
        head.set_payload('Version: 1')
        msg.attach(head)
        body = MIMEBase('application', 'octet-stream')
        body.set_payload(encrypted_msg.data)
        msg.attach(body)

        return msg

    def check_pubkey(self, recipient):
        keys = list()

        # Tricks to flatten list of list of mails
        [ keys.extend(key['uids']) for key in self.gpg.list_keys() ]

        for key in keys:
            if key.find(recipient) != -1:
                return True

        return False

def test():
    recipients = ['test@example.com']
    mailer = Mailer('me@example.com',
        gpghome='/home/user/.gpg',
        server='smtp.example.com')

    mailer.send_mail(
            recipients,
            'test',
            'test',
            files=['./file', './access.zip', ],
            encrypted=True,
            )

if __name__ == '__main__':
    test()
