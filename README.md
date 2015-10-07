# sample-django-app
This is just my sample django app... I am sharing this because it is avaliable only localy (intranet), 
and changed some sensitive data (passwords, IPs, domain names, etc). 
It isn't perfect (for example there are no unittests) because the budget was realy limited, so I didn't have 
much time for making this perfect.

It is just dashboard (the main part of this application are management scripts in indexer/management/commands - 
they are plugable from UI so it is a tool for executing custom tasks (written in specific format),
monitoring the progress, tracking issues, that are able to manage big dataset (milions of records).

You can also find here:
* some django backend for distributed MogileFS (utils/mogile_multistorage.py)
* relationalDB<=>mongoDB synchroniser (utils.utils.MongoSynchronizer)
* some advanced image processing (Pillow: composing transparent images)
* creating transparent images alghorithm (indexer/management/commands/switch_to_transparent.py), 
* conveinient tool for creating thumbnails (utils/utils.py).
* some tool similar to haystack (works with SOLR that was set up manually) -it isn't finished,
but maybe it is a good idea to start working on that
