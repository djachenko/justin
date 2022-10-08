import json
from datetime import date

CLOSED_NAMES = {
    "": [
        "annette",
        "cactus",
        "cafe",
        "family",
        "fen",
        "fit",
        "hikkas_eve",
        "issc",
        "kotikit",
        "leonova",
        "lika",
        "luci",
        "maximin",
        "palliative",
        "pesterev",
        "photoclub",
        "private",
        "roof",
        "rudevskaya",
        "sessions",
        "shabanov",
        "sibfm",
        "technologika",
        "volgina",
        "grebennikov",
        "rats",
        "shurunova",
        "ursul",
        "comein",
        "td",
        "td_chelyabinsk",
        "td_yalta",

        "subacheva",
        "meeting_place",
        "self",
    ],

    "20.10.27.openbio_day1": [
        "openbio", ],

    "20.10.17.td_piter": [
        "td_piter",
    ],

    "20.10.15.justin_meetup_comein": [
        "justin_meetup",

    ],

    "20.06.13.lada_lesson": [
        "sorokina",

    ],

    "refactoring structure": [
        "dad",
        "mom",

    ],

    "20.07.10.fj_prom": [
        "fj",

    ],

    "21.01.24.music_club_pianista": [
        "music_club",

    ],

    "21.02.musica_integral": [
        "musica_integral",

    ],

    "19.07.10.fit_graduation": [
        "farafonova",

    ],

    "18.08.08.yakovleva_session": [
        "yakovleva",

    ],

    "18.08.04.banya": [
        "yurchenko",

    ],

    "21.04.12.zinina_walk": [
        "zinina",

    ],

    "21.07.04.perf_concert": [
        "nsu_orchestra",

    ],

    "21.08.07.graphit_archive": [
        "graphit",

    ],

    "20.11.02.samuseva_cup": [
        "my_people",

    ],

    "21.04.10.firesession": [
        "nsu_fire",

    ],

    "21.07.01.frolova_prom": [
        "frolova",

    ],

    "21.07.09.samuseva_walk": [
        "samuseva",

    ],

    "21.07.11.freebus_clip_backstage": [
        "free_bus",

    ],

    "22.06.24.bakina_prom": [
        "bakina",

    ],

    "22.07.14.tensor_girls_photoset": [
        "chusovkova",
        "khlimankova",
        "pogrebnikova",
    ]
}

#   CLOSED_NAMES

MY_PEOPLE_NEW = {
    "22.05.01.ffals_init": [
        ("bondareva", "Арина Бондарева", 538017452),
        ("iskova", "Анастасия Искова", 238713585),
        ("petrova", "", 0),
        ("ponomareva_tanya", "", 0),
        ("pudova", "", 0),
        ("rukomoynikova", "", 0),
        ("schelkanova", "", 0),
        ("shmakova", "", 0),
        ("sibiryakova", "", 0),
        ("sinyaeva", "", 0),
        ("stetsky", "", 0),
        ("terekhova", "", 0),
        ("tolstikova", "", 0),
        ("vostrikova", "", 0),
    ]

}

# noinspection SpellCheckingInspection
MY_PEOPLE_NAMES = {
    "": [
        "absaidulieva",
        "ahmary",
        "anischenko",
        "annette",
        "antipova",
        "asadchaya",
        "aziza",
        "babich_duplicate",
        "babicheva",
        "banan",
        "belovezhets",
        "biryukov",
        "biserova",
        "budaeva",
        "cafe",
        "community",
        "contest",
        "damdinov",
        "dubynina",
        "ermishina",
        "esler",
        "faina",
        "fokina",
        "frolova",
        "gapenko",
        "gassan",
        "golodyaeva",
        "gryzova",
        "guzhvina",
        "iokimaru",
        "kachanova",
        "kamaeva",
        "karmanova",
        "kolpakov",
        "korobova",
        "kosikhin",
        "leonova",
        "lika",
        "lina",
        "self",
        "melgunov",
        "miroshnichenko",
        "nam",
        "nastya_med",
        "nigga",
        "okhvat",
        "oydopova",
        "pesterev",
        "photoclub",
        "porechnaya_ggf",
        "rats",
        "sazhina",
        "sharipova",
        "sher",
        "shkel",
        "shlee",
        "shmakov",
        "spice",
        "toropova",
        "van_kooij",
        "vesnina",
        "yartseva",
        "zimbickiy",
        "arkhipova",
        "boguk",
        "fen_redhead",
        "nazarov",
        "belaya",
        "ershova",
        "farafonova",
        "gorovits",
        "khromov",
        "rudevskaya",
        "balashova",
        "cheerleaders",
        "dutta",
        "golubeva",
        "kashtakova",
        "batanova",
        "bezrukova",
        "bobrova",
        "davydenko",
        "ganzenko",
        "guritskaya",
        "keplin",
        "kirpichyova",
        "kobozova",
        "kolpakova",
        "kovalenko",
        "kuznetsova",
        "kuznetsova_vera",
        "makk",
        "mayboroda",
        "mironov",
        "murashova",
        "mustakova",
        "pershechkina",
        "rush",
        "safarova",
        "sekretarenko",
        "sergeeva",
        "shatalova",
        "tokmakova",
        "vinokurov",
        "volgina",
        "yaroshenko",

    ],

    "19.10.??.cactus_halloween": [
        "zherebtsova",
        "doronin",

    ],

    "19.12.01.fit_fija_init_we_are_young": [
        "bayramov",
        "dyuganov",
        "khayatova",
        "kunitskaya",
        "shabanov",

    ],

    "20.03.??.fen_init": [
        "ageenko",
        "aleksandrova_nastya",
        "black",
        "cherchik",
        "chernyak",
        "datta",
        "dmitrieva_nastya",
        "elsukova",
        "khozeeva",
        "kolobova",
        "kovaleva",
        "mogilnaya",
        "okhina",
        "osipov",
        "peretyatko",
        "potapenko",
        "subacheva",
        "unknown",
        "yakovleva",

    ],

    "19.09.2?.fen_init_hell": [
        "dolgushev",
        "kakhkharova",
        "ludens",
        "moklyak",
        "morozova",
        "pobedintseva",
        "skrypnik",
        "vokhidov",

    ],

    "19.10.??.fj_init_forest": [
        "abdullaeva",
        "muravyova",
        "pikulina",
        "derevnina",
        "ganzha",
        "khlevnaya",
        "kozlova",
        "larina",
        "lozovaya",
        "oleynikova",
        "radina",
        "shestakova",
        "shlyapuzhnikova",
        "varlamova",
        "verkhovinskaya",
        "black_list",

    ],

    "19.09.14.night_in_nsu": [
        "dityuk",
        "efremova",
        "azarova",
        "ignatyeva",
        "manyutin",
        "baburina",

    ],

    "19.09.14.fire_show": [
        "mikhaylov",

    ],

    "19.09.14.chemistry_experiments": [
        "rudenko",

    ],

    "19.08.??.obviousness": [
        "samsonova",

    ],

    "19.09.01.akagem": [
        "averina",
        "bugaeva",
        "kireytseva",
        "politina",
        "salekhi",
        "smal",

    ],

    "19.09.??.guess_for_three": [
        "bykova",
        "nalivkin",
        "sukhinina",
        "yakushenko",

    ],

    "19.09.??.sentyabrevka": [
        "zepsan",
        "kuprianova",
        "lemberg",
        "pozhidaeva",
        "sazhina_elena",
        "firsova",
        "nenasheva",
        "obelenets",
        "shishkina",
        "zhizhin",

    ],

    "20.02.29.maslenitsa": [
        "efremidi",

    ],

    "19.12.01.fit_fija_init_forest": [
        "akinina",
        "ayupova",
        "fugenfirova",
        "klimonova",
        "legostaeva",
        "leontyeva",
        "pershikova",

    ],

    "19.10.13.ff_init": [
        "antonova",
        "golovina",
        "kharchenko",
        "labuntsov",
        "mirgazizova",
        "nikolaev",
        "onopchenko",
        "ostapchenko",
        "savelyeva",
        "smirnova",
        "tintulova",
        "ugdyzhekova",
        "vladyko",
        "yartseva_maria",

    ],

    "19.09.11.sentyabrevka": [
        "lvov",

    ],

    "19.02.02.td_conference_day3": [
        "kalinina",
        "kalinistova",
        "kostyreva",
        "lukyanova",
        "ognev",

    ],

    "16.04.30.arbat": [
        "elkhovskaya",
        "ivanov",
        "khotkina",

    ],

    "16.04.30.maevka": [
        "dorozhko",
        "gornostaeva",
        "ivannikova",
        "ivanova_lina",
        "mukhin",
        "ostanina",
        "tsupa",
        "valentinasov",

    ],

    "19.03.03.fen_init": [
        "drozdova",

    ],

    "20.10.27.openbio_day1": [
        "kravchenko",
        "purvinsh_yana",
        "kononova_polina",
        "linyushina",

    ],

    "20.10.27.openbio_day4": [
        "osmak",

    ],

    "20.10.31.cactus_halloween": [
        "boikova",
        "reznikov",

    ],

    "20.09.12.console": [
        "saraeva",
        "snegireva",
        "voloshina",

    ],

    "20.08.19.kvartirnik_gusi": [
        "antsiforova",
        "kanaeva",
        "tarkhanova",

    ],

    "20.08.22.dogvartirnik": [
        "prokopyeva",

    ],

    "20.09.01.domenik": [
        "bokarev",
        "brovanova",
        "krasilova",
        "kvartira",
        "melyokhina",
        "menshe_3",
        "zavyalov",

    ],

    "20.12.05.miss_stc": [
        "kotikit",
        "merkulova",
        "petrenko",
        "prokhoshin",
        "ulybina",
        "zinnatova",

    ],

    "20.12.05.fit_quest": [
        "golovnina",
        "karavaev",
        "kolomnikova",

    ],

    "21.01.30.dekadent": [
        "rozenberg",
        "salamcheva",

    ],

    "21.01.24.music_club_pianista": [
        "music_club",

    ],

    "21.02.musica_integral": [
        "musica_integral",
        "strelets",

    ],

    "21.03.07.quant_eveninger": [
        "gervaziev",
        "malyarevich",
        "vinri",
        "vishnevskaya",

    ],


    "19.07.10.fit_graduation": [
        "kosogova",
        "zavalishina",

    ],

    "21.07.11.graphit_nauki": [
        "erokhin",
        "tumina",
        "samuseva",

    ],

    "21.04.10.totaldict": [
        "bliznyuk",
        "okhotin",
        "vlasova",

    ],

    "21.06.26.fj_garazhka": [
        "botsmanov",
        "sobolina",

    ],

    "21.03.30.antiscience": [
        "nurislamov",

    ],

    "21.06.12.vinri_concert": [
        "krymov",

    ],

    "22.04.30.vivaldi_catholic": [
        "davydova",
        "markova",
        "niyazov",
        "paraschevina",
        "sapogova",

    ],

    "22.05.01.ffals_init": [
        "kudryashova",
        "idyrysov",

    ],

    "22.05.14.self_maevka": [
        "alyokhina",
        "arkhipenko",
        "baydak",
        "bespalova",
        "gubina",
        "kononova",
        "kupriyanova",
        "zhilina",

    ],

    "22.05.29.for_me_clever": [
        "evdokimova",
        "gri",
        "for_me",
        "kishina",
        "poplavskaya",
        "savilova",
        "serova",
        "slastnaya",
        "zhurkina",

    ],

    "22.06.24.bakina_prom": [
        "bakina",
        "belitsa",
        "ermakova",
        "mezentseva",
        "shashev",
        "shumskaya",
    ]
}

if __name__ == '__main__':
    people = []
    register_date = date.today()

    for source, names in MY_PEOPLE_NAMES.items():
        for name in names:
            d = {
                "folder": name,
                "name": None,
                "vk_id": None,
                "source": source,
                "register_date": register_date.isoformat(),
            }

            people.append(d)

    for source, names in MY_PEOPLE_NEW.items():
        for folder, name, vk_id in names:
            d = {
                "folder": folder,
                "name": name,
                "vk_id": vk_id,
                "source": source,
                "register_date": register_date.isoformat(),
            }

            people.append(d)

    print(json.dumps(people, indent=4, ensure_ascii=False))


