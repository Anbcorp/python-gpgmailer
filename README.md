Helper class to send gpg encrypted mail to single or multiple recipients.

  * Support attachement as per RFC3156
  * Public key management must be handled by hand using gpg tools.

Typical Usage
=============

```python
from mailer import Mailer

mailr = Mailer(
    sent_from="me@mydomain.com",
    gpghome="/home/me/.gpg",
    server="smtp.mydomain.com"
    )

recipients = ['joe@doe.com', 'alice@example.net', 'bob@example.net']

# filter out recipients that we do not have a pubkey for
valid_recipients = [ recipient for recipient in recipients 
                        if mailer.valid_pubkey(recipient) ]

attachements = ['funny_kitten.gif', 'doge_meme.png']


msg = """
Hi,

Found those funny images, check them out !

Very kitteh, such funny.

Live long and prosper,
"""

mailr.send_mail(
    valid_recipients,
    'Check those funny images',
    msg,
    attachements)
```
