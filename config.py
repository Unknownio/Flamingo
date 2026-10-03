# config.py

DATA_BROKERS = [
    # Group 1: Major People Search
    "spokeo.com", "whitepages.com", "radaris.com", "fastpeoplesearch.com", "truepeoplesearch.com",
    # Group 2: Aggregators
    "beenverified.com", "peoplelooker.com", "thatsthem.com", "nuwber.com", "searchpeoplefree.com",
    # Group 3: Background Checkers
    "cyberbackgroundchecks.com", "instantcheckmate.com", "truthfinder.com", "intelius.com", "checkpeople.com",
    # Group 4: Directories
    "peekyou.com", "zabasearch.com", "ussearch.com", "familytreenow.com", "usphonebook.com",
    # Group 5: Address & Phone
    "clustrmaps.com", "addresssearch.com", "anywho.com", "411.com", "spytox.com",
    # Group 6: Public & Voter Records
    "cubib.com", "voterrecords.com", "publicrecords360.com", "yellowpages.com", "smartfastfinder.com"
]

OPT_OUT_LINKS = {
    "spokeo.com": "https://www.spokeo.com/optout",
    "whitepages.com": "https://www.whitepages.com/suppression-requests",
    "radaris.com": "https://radaris.com/page/opt-out",
    "fastpeoplesearch.com": "https://www.fastpeoplesearch.com/removal",
    "truepeoplesearch.com": "https://www.truepeoplesearch.com/removal",
    "beenverified.com": "https://www.beenverified.com/app/optout/search",
    "peoplelooker.com": "https://www.peoplelooker.com/f/optout/search",
    "thatsthem.com": "https://thatsthem.com/optout",
    "nuwber.com": "https://nuwber.com/removal/link",
    "searchpeoplefree.com": "https://www.searchpeoplefree.com/opt-out",
    "cyberbackgroundchecks.com": "https://www.cyberbackgroundchecks.com/removal",
    "instantcheckmate.com": "https://www.instantcheckmate.com/opt-out/",
    "truthfinder.com": "https://www.truthfinder.com/opt-out/",
    "intelius.com": "https://www.intelius.com/opt-out/",
    "checkpeople.com": "https://checkpeople.com/opt-out",
    "peekyou.com": "https://www.peekyou.com/about/contact/optout/",
    "zabasearch.com": "https://www.zabasearch.com/block_records/",
    "ussearch.com": "https://www.ussearch.com/opt-out/",
    "familytreenow.com": "https://www.familytreenow.com/optout",
    "usphonebook.com": "https://www.usphonebook.com/opt-out",
    "clustrmaps.com": "https://clustrmaps.com/bl/opt-out",
    "addresssearch.com": "https://www.addresssearch.com/remove-name.php",
    "anywho.com": "https://www.anywho.com/optout",
    "411.com": "https://www.411.com/opt-out",
    "spytox.com": "https://www.spytox.com/optout",
    "cubib.com": "https://cubib.com/optout.php",
    "voterrecords.com": "https://voterrecords.com/optout",
    "publicrecords360.com": "https://www.publicrecords360.com/optout",
    "yellowpages.com": "https://www.yellowpages.com/about/opt-out",
    "smartfastfinder.com": "https://smartfastfinder.com/optout"
}

DORK_SITES = [
    "pastebin.com", "ghostbin.com", "rentry.co", "justpaste.it"
]