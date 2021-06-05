"""
tests.files
===========

Content to write to mock files.
"""
# pylint: disable=too-many-lines

README_RST = """repo\n====\n"""
INDEX_RST = """
Repo
====

|

The source code is available `here <https://github.com/johndoe/repo>`_

|

.. toctree::
   :maxdepth: 1
   :name: mastertoc

   repo
   readme

* :ref:`genindex`

This documentation was last updated on |today|
"""
PIPFILE_LOCK = """{
{
    "_meta": {
        "hash": {
            "sha256": "b0396f47f63aa3a62e379a0c7b6c8044aa27db438688d9e3e4749b91cea58054"
        },
        "pipfile-spec": 6,
        "requires": {
            "python_version": "3.8"
        },
        "sources": [
            {
                "name": "pypi",
                "url": "https://pypi.org/simple",
                "verify_ssl": true
            }
        ]
    },
    "default": {
        "alabaster": {
            "hashes": [
                "sha256:446438bdcca0e05bd45ea2de1668c1d9b032e1a9154c2c259092d77031ddd359",
                "sha256:a661d72d58e6ea8a57f7a86e37d86716863ee5e92788398526d58b26a4e4dc02"
            ],
            "version": "==0.7.12"
        },
        "appdirs": {
            "hashes": [
                "sha256:7d5d0167b2b1ba821647616af46a749d1c653740dd0d2415100fe26e27afdf41",
                "sha256:a841dacd6b99318a741b166adb07e19ee71a274450e68237b4650ca1055ab128"
            ],
            "index": "pypi",
            "version": "==1.4.4"
        },
        "astroid": {
            "hashes": [
                "sha256:2f4078c2a41bf377eea06d71c9d2ba4eb8f6b1af2135bec27bbbb7d8f12bb703",
                "sha256:bc58d83eb610252fd8de6363e39d4f1d0619c894b0ed24603b881c02e64c7386"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==2.4.2"
        },
        "attrs": {
            "hashes": [
                "sha256:31b2eced602aa8423c2aea9c76a724617ed67cf9513173fd3a4f03e3a929c7e6",
                "sha256:832aa3cde19744e49938b91fea06d69ecb9e649c93ba974535d08ad92164f700"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==20.3.0"
        },
        "babel": {
            "hashes": [
                "sha256:9d35c22fcc79893c3ecc85ac4a56cde1ecf3f19c540bba0922308a6c06ca6fa5",
                "sha256:da031ab54472314f210b0adcff1588ee5d1d1d0ba4dbd07b94dba82bde791e05"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==2.9.0"
        },
        "black": {
            "hashes": [
                "sha256:1c02557aa099101b9d21496f8a914e9ed2222ef70336404eeeac8edba836fbea"
            ],
            "index": "pypi",
            "version": "==20.8b1"
        },
        "certifi": {
            "hashes": [
                "sha256:1a4995114262bffbc2413b159f2a1a480c969de6e6eb13ee966d470af86af59c",
                "sha256:719a74fb9e33b9bd44cc7f3a8d94bc35e4049deebe19ba7d8e108280cfd59830"
            ],
            "version": "==2020.12.5"
        },
        "chardet": {
            "hashes": [
                "sha256:0d6f53a15db4120f2b08c94f11e7d93d2c911ee118b6b30a04ec3ee8310179fa",
                "sha256:f864054d66fd9118f2e67044ac8981a54775ec5b67aed0441892edb553d21da5"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==4.0.0"
        },
        "click": {
            "hashes": [
                "sha256:d2b5255c7c6349bc1bd1e59e08cd12acbbd63ce649f2588755783aa94dfb6b1a",
                "sha256:dacca89f4bfadd5de3d7489b7c8a566eee0d3676333fbb50030263894c38c0dc"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==7.1.2"
        },
        "codecov": {
            "hashes": [
                "sha256:6cde272454009d27355f9434f4e49f238c0273b216beda8472a65dc4957f473b",
                "sha256:ba8553a82942ce37d4da92b70ffd6d54cf635fc1793ab0a7dc3fecd6ebfb3df8",
                "sha256:e95901d4350e99fc39c8353efa450050d2446c55bac91d90fcfd2354e19a6aef"
            ],
            "index": "pypi",
            "version": "==2.1.11"
        },
        "coverage": {
            "extras": [
                "toml"
            ],
            "hashes": [
                "sha256:08b3ba72bd981531fd557f67beee376d6700fba183b167857038997ba30dd297",
                "sha256:2757fa64e11ec12220968f65d086b7a29b6583d16e9a544c889b22ba98555ef1",
                "sha256:3102bb2c206700a7d28181dbe04d66b30780cde1d1c02c5f3c165cf3d2489497",
                "sha256:3498b27d8236057def41de3585f317abae235dd3a11d33e01736ffedb2ef8606",
                "sha256:378ac77af41350a8c6b8801a66021b52da8a05fd77e578b7380e876c0ce4f528",
                "sha256:38f16b1317b8dd82df67ed5daa5f5e7c959e46579840d77a67a4ceb9cef0a50b",
                "sha256:3911c2ef96e5ddc748a3c8b4702c61986628bb719b8378bf1e4a6184bbd48fe4",
                "sha256:3a3c3f8863255f3c31db3889f8055989527173ef6192a283eb6f4db3c579d830",
                "sha256:3b14b1da110ea50c8bcbadc3b82c3933974dbeea1832e814aab93ca1163cd4c1",
                "sha256:535dc1e6e68fad5355f9984d5637c33badbdc987b0c0d303ee95a6c979c9516f",
                "sha256:6f61319e33222591f885c598e3e24f6a4be3533c1d70c19e0dc59e83a71ce27d",
                "sha256:723d22d324e7997a651478e9c5a3120a0ecbc9a7e94071f7e1954562a8806cf3",
                "sha256:76b2775dda7e78680d688daabcb485dc87cf5e3184a0b3e012e1d40e38527cc8",
                "sha256:782a5c7df9f91979a7a21792e09b34a658058896628217ae6362088b123c8500",
                "sha256:7e4d159021c2029b958b2363abec4a11db0ce8cd43abb0d9ce44284cb97217e7",
                "sha256:8dacc4073c359f40fcf73aede8428c35f84639baad7e1b46fce5ab7a8a7be4bb",
                "sha256:8f33d1156241c43755137288dea619105477961cfa7e47f48dbf96bc2c30720b",
                "sha256:8ffd4b204d7de77b5dd558cdff986a8274796a1e57813ed005b33fd97e29f059",
                "sha256:93a280c9eb736a0dcca19296f3c30c720cb41a71b1f9e617f341f0a8e791a69b",
                "sha256:9a4f66259bdd6964d8cf26142733c81fb562252db74ea367d9beb4f815478e72",
                "sha256:9a9d4ff06804920388aab69c5ea8a77525cf165356db70131616acd269e19b36",
                "sha256:a2070c5affdb3a5e751f24208c5c4f3d5f008fa04d28731416e023c93b275277",
                "sha256:a4857f7e2bc6921dbd487c5c88b84f5633de3e7d416c4dc0bb70256775551a6c",
                "sha256:a607ae05b6c96057ba86c811d9c43423f35e03874ffb03fbdcd45e0637e8b631",
                "sha256:a66ca3bdf21c653e47f726ca57f46ba7fc1f260ad99ba783acc3e58e3ebdb9ff",
                "sha256:ab110c48bc3d97b4d19af41865e14531f300b482da21783fdaacd159251890e8",
                "sha256:b239711e774c8eb910e9b1ac719f02f5ae4bf35fa0420f438cdc3a7e4e7dd6ec",
                "sha256:be0416074d7f253865bb67630cf7210cbc14eb05f4099cc0f82430135aaa7a3b",
                "sha256:c46643970dff9f5c976c6512fd35768c4a3819f01f61169d8cdac3f9290903b7",
                "sha256:c5ec71fd4a43b6d84ddb88c1df94572479d9a26ef3f150cef3dacefecf888105",
                "sha256:c6e5174f8ca585755988bc278c8bb5d02d9dc2e971591ef4a1baabdf2d99589b",
                "sha256:c89b558f8a9a5a6f2cfc923c304d49f0ce629c3bd85cb442ca258ec20366394c",
                "sha256:cc44e3545d908ecf3e5773266c487ad1877be718d9dc65fc7eb6e7d14960985b",
                "sha256:cc6f8246e74dd210d7e2b56c76ceaba1cc52b025cd75dbe96eb48791e0250e98",
                "sha256:cd556c79ad665faeae28020a0ab3bda6cd47d94bec48e36970719b0b86e4dcf4",
                "sha256:ce6f3a147b4b1a8b09aae48517ae91139b1b010c5f36423fa2b866a8b23df879",
                "sha256:ceb499d2b3d1d7b7ba23abe8bf26df5f06ba8c71127f188333dddcf356b4b63f",
                "sha256:cef06fb382557f66d81d804230c11ab292d94b840b3cb7bf4450778377b592f4",
                "sha256:e448f56cfeae7b1b3b5bcd99bb377cde7c4eb1970a525c770720a352bc4c8044",
                "sha256:e52d3d95df81c8f6b2a1685aabffadf2d2d9ad97203a40f8d61e51b70f191e4e",
                "sha256:ee2f1d1c223c3d2c24e3afbb2dd38be3f03b1a8d6a83ee3d9eb8c36a52bee899",
                "sha256:f2c6888eada180814b8583c3e793f3f343a692fc802546eed45f40a001b1169f",
                "sha256:f51dbba78d68a44e99d484ca8c8f604f17e957c1ca09c3ebc2c7e3bbd9ba0448",
                "sha256:f54de00baf200b4539a5a092a759f000b5f45fd226d6d25a76b0dff71177a714",
                "sha256:fa10fee7e32213f5c7b0d6428ea92e3a3fdd6d725590238a3f92c0de1c78b9d2",
                "sha256:fabeeb121735d47d8eab8671b6b031ce08514c86b7ad8f7d5490a7b6dcd6267d",
                "sha256:fac3c432851038b3e6afe086f777732bcf7f6ebbfd90951fa04ee53db6d0bcdd",
                "sha256:fda29412a66099af6d6de0baa6bd7c52674de177ec2ad2630ca264142d69c6c7",
                "sha256:ff1330e8bc996570221b450e2d539134baa9465f5cb98aff0e0f73f34172e0ae"
            ],
            "index": "pypi",
            "version": "==5.3.1"
        },
        "docutils": {
            "hashes": [
                "sha256:0c5b78adfbf7762415433f5515cd5c9e762339e23369dbe8000d84a4bf4ab3af",
                "sha256:c2de3a60e9e7d07be26b7f2b00ca0309c207e06c100f9cc2a94931fc75a478fc"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==0.16"
        },
        "gprof2dot": {
            "hashes": [
                "sha256:b43fe04ebb3dfe181a612bbfc69e90555b8957022ad6a466f0308ed9c7f22e99"
            ],
            "version": "==2019.11.30"
        },
        "idna": {
            "hashes": [
                "sha256:b307872f855b18632ce0c21c5e45be78c0ea7ae4c15c828c20788b26921eb3f6",
                "sha256:b97d804b1e9b523befed77c48dacec60e6dcb0b5391d57af6a65a312a90648c0"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==2.10"
        },
        "imagesize": {
            "hashes": [
                "sha256:6965f19a6a2039c7d48bca7dba2473069ff854c36ae6f19d2cde309d998228a1",
                "sha256:b1f6b5a4eab1f73479a50fb79fcf729514a900c341d8503d62a62dbc4127a2b1"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.2.0"
        },
        "iniconfig": {
            "hashes": [
                "sha256:011e24c64b7f47f6ebd835bb12a743f2fbe9a26d4cecaa7f53bc4f35ee9da8b3",
                "sha256:bc3af051d7d14b2ee5ef9969666def0cd1a000e121eaea580d4a313df4b37f32"
            ],
            "version": "==1.1.1"
        },
        "isort": {
            "hashes": [
                "sha256:c729845434366216d320e936b8ad6f9d681aab72dc7cbc2d51bedc3582f3ad1e",
                "sha256:fff4f0c04e1825522ce6949973e83110a6e907750cd92d128b0d14aaaadbffdc"
            ],
            "markers": "python_version >= '3.6' and python_version < '4.0'",
            "version": "==5.7.0"
        },
        "jinja2": {
            "hashes": [
                "sha256:89aab215427ef59c34ad58735269eb58b1a5808103067f7bb9d5836c651b3bb0",
                "sha256:f0a4641d3cf955324a89c04f3d94663aa4d638abe8f733ecd3582848e1c37035"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==2.11.2"
        },
        "lazy-object-proxy": {
            "hashes": [
                "sha256:0c4b206227a8097f05c4dbdd323c50edf81f15db3b8dc064d08c62d37e1a504d",
                "sha256:194d092e6f246b906e8f70884e620e459fc54db3259e60cf69a4d66c3fda3449",
                "sha256:1be7e4c9f96948003609aa6c974ae59830a6baecc5376c25c92d7d697e684c08",
                "sha256:4677f594e474c91da97f489fea5b7daa17b5517190899cf213697e48d3902f5a",
                "sha256:48dab84ebd4831077b150572aec802f303117c8cc5c871e182447281ebf3ac50",
                "sha256:5541cada25cd173702dbd99f8e22434105456314462326f06dba3e180f203dfd",
                "sha256:59f79fef100b09564bc2df42ea2d8d21a64fdcda64979c0fa3db7bdaabaf6239",
                "sha256:8d859b89baf8ef7f8bc6b00aa20316483d67f0b1cbf422f5b4dc56701c8f2ffb",
                "sha256:9254f4358b9b541e3441b007a0ea0764b9d056afdeafc1a5569eee1cc6c1b9ea",
                "sha256:9651375199045a358eb6741df3e02a651e0330be090b3bc79f6d0de31a80ec3e",
                "sha256:97bb5884f6f1cdce0099f86b907aa41c970c3c672ac8b9c8352789e103cf3156",
                "sha256:9b15f3f4c0f35727d3a0fba4b770b3c4ebbb1fa907dbcc046a1d2799f3edd142",
                "sha256:a2238e9d1bb71a56cd710611a1614d1194dc10a175c1e08d75e1a7bcc250d442",
                "sha256:a6ae12d08c0bf9909ce12385803a543bfe99b95fe01e752536a60af2b7797c62",
                "sha256:ca0a928a3ddbc5725be2dd1cf895ec0a254798915fb3a36af0964a0a4149e3db",
                "sha256:cb2c7c57005a6804ab66f106ceb8482da55f5314b7fcb06551db1edae4ad1531",
                "sha256:d74bb8693bf9cf75ac3b47a54d716bbb1a92648d5f781fc799347cfc95952383",
                "sha256:d945239a5639b3ff35b70a88c5f2f491913eb94871780ebfabb2568bd58afc5a",
                "sha256:eba7011090323c1dadf18b3b689845fd96a61ba0a1dfbd7f24b921398affc357",
                "sha256:efa1909120ce98bbb3777e8b6f92237f5d5c8ea6758efea36a473e1d38f7d3e4",
                "sha256:f3900e8a5de27447acbf900b4750b0ddfd7ec1ea7fbaf11dfa911141bc522af0"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.4.3"
        },
        "markupsafe": {
            "hashes": [
                "sha256:00bc623926325b26bb9605ae9eae8a215691f33cae5df11ca5424f06f2d1f473",
                "sha256:09027a7803a62ca78792ad89403b1b7a73a01c8cb65909cd876f7fcebd79b161",
                "sha256:09c4b7f37d6c648cb13f9230d847adf22f8171b1ccc4d5682398e77f40309235",
                "sha256:1027c282dad077d0bae18be6794e6b6b8c91d58ed8a8d89a89d59693b9131db5",
                "sha256:13d3144e1e340870b25e7b10b98d779608c02016d5184cfb9927a9f10c689f42",
                "sha256:24982cc2533820871eba85ba648cd53d8623687ff11cbb805be4ff7b4c971aff",
                "sha256:29872e92839765e546828bb7754a68c418d927cd064fd4708fab9fe9c8bb116b",
                "sha256:43a55c2930bbc139570ac2452adf3d70cdbb3cfe5912c71cdce1c2c6bbd9c5d1",
                "sha256:46c99d2de99945ec5cb54f23c8cd5689f6d7177305ebff350a58ce5f8de1669e",
                "sha256:500d4957e52ddc3351cabf489e79c91c17f6e0899158447047588650b5e69183",
                "sha256:535f6fc4d397c1563d08b88e485c3496cf5784e927af890fb3c3aac7f933ec66",
                "sha256:596510de112c685489095da617b5bcbbac7dd6384aeebeda4df6025d0256a81b",
                "sha256:62fe6c95e3ec8a7fad637b7f3d372c15ec1caa01ab47926cfdf7a75b40e0eac1",
                "sha256:6788b695d50a51edb699cb55e35487e430fa21f1ed838122d722e0ff0ac5ba15",
                "sha256:6dd73240d2af64df90aa7c4e7481e23825ea70af4b4922f8ede5b9e35f78a3b1",
                "sha256:717ba8fe3ae9cc0006d7c451f0bb265ee07739daf76355d06366154ee68d221e",
                "sha256:79855e1c5b8da654cf486b830bd42c06e8780cea587384cf6545b7d9ac013a0b",
                "sha256:7c1699dfe0cf8ff607dbdcc1e9b9af1755371f92a68f706051cc8c37d447c905",
                "sha256:88e5fcfb52ee7b911e8bb6d6aa2fd21fbecc674eadd44118a9cc3863f938e735",
                "sha256:8defac2f2ccd6805ebf65f5eeb132adcf2ab57aa11fdf4c0dd5169a004710e7d",
                "sha256:98c7086708b163d425c67c7a91bad6e466bb99d797aa64f965e9d25c12111a5e",
                "sha256:9add70b36c5666a2ed02b43b335fe19002ee5235efd4b8a89bfcf9005bebac0d",
                "sha256:9bf40443012702a1d2070043cb6291650a0841ece432556f784f004937f0f32c",
                "sha256:ade5e387d2ad0d7ebf59146cc00c8044acbd863725f887353a10df825fc8ae21",
                "sha256:b00c1de48212e4cc9603895652c5c410df699856a2853135b3967591e4beebc2",
                "sha256:b1282f8c00509d99fef04d8ba936b156d419be841854fe901d8ae224c59f0be5",
                "sha256:b2051432115498d3562c084a49bba65d97cf251f5a331c64a12ee7e04dacc51b",
                "sha256:ba59edeaa2fc6114428f1637ffff42da1e311e29382d81b339c1817d37ec93c6",
                "sha256:c8716a48d94b06bb3b2524c2b77e055fb313aeb4ea620c8dd03a105574ba704f",
                "sha256:cd5df75523866410809ca100dc9681e301e3c27567cf498077e8551b6d20e42f",
                "sha256:cdb132fc825c38e1aeec2c8aa9338310d29d337bebbd7baa06889d09a60a1fa2",
                "sha256:e249096428b3ae81b08327a63a485ad0878de3fb939049038579ac0ef61e17e7",
                "sha256:e8313f01ba26fbbe36c7be1966a7b7424942f670f38e666995b88d012765b9be"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.1.1"
        },
        "mccabe": {
            "hashes": [
                "sha256:ab8a6258860da4b6677da4bd2fe5dc2c659cff31b3ee4f7f5d64e79735b80d42",
                "sha256:dd8d182285a0fe56bace7f45b5e7d1a6ebcbf524e8f3bd87eb0f125271b8831f"
            ],
            "version": "==0.6.1"
        },
        "mypy": {
            "hashes": [
                "sha256:0d2fc8beb99cd88f2d7e20d69131353053fbecea17904ee6f0348759302c52fa",
                "sha256:2b216eacca0ec0ee124af9429bfd858d5619a0725ee5f88057e6e076f9eb1a7b",
                "sha256:319ee5c248a7c3f94477f92a729b7ab06bf8a6d04447ef3aa8c9ba2aa47c6dcf",
                "sha256:3e0c159a7853e3521e3f582adb1f3eac66d0b0639d434278e2867af3a8c62653",
                "sha256:5615785d3e2f4f03ab7697983d82c4b98af5c321614f51b8f1034eb9ebe48363",
                "sha256:5ff616787122774f510caeb7b980542a7cc2222be3f00837a304ea85cd56e488",
                "sha256:6f8425fecd2ba6007e526209bb985ce7f49ed0d2ac1cc1a44f243380a06a84fb",
                "sha256:74f5aa50d0866bc6fb8e213441c41e466c86678c800700b87b012ed11c0a13e0",
                "sha256:90b6f46dc2181d74f80617deca611925d7e63007cf416397358aa42efb593e07",
                "sha256:947126195bfe4709c360e89b40114c6746ae248f04d379dca6f6ab677aa07641",
                "sha256:a301da58d566aca05f8f449403c710c50a9860782148332322decf73a603280b",
                "sha256:aa9d4901f3ee1a986a3a79fe079ffbf7f999478c281376f48faa31daaa814e86",
                "sha256:b9150db14a48a8fa114189bfe49baccdff89da8c6639c2717750c7ae62316738",
                "sha256:b95068a3ce3b50332c40e31a955653be245666a4bc7819d3c8898aa9fb9ea496",
                "sha256:ca7ad5aed210841f1e77f5f2f7d725b62c78fa77519312042c719ed2ab937876",
                "sha256:d16c54b0dffb861dc6318a8730952265876d90c5101085a4bc56913e8521ba19",
                "sha256:e0202e37756ed09daf4b0ba64ad2c245d357659e014c3f51d8cd0681ba66940a",
                "sha256:e1c84c65ff6d69fb42958ece5b1255394714e0aac4df5ffe151bc4fe19c7600a",
                "sha256:e32b7b282c4ed4e378bba8b8dfa08e1cfa6f6574067ef22f86bee5b1039de0c9",
                "sha256:e3b8432f8df19e3c11235c4563a7250666dc9aa7cdda58d21b4177b20256ca9f",
                "sha256:e497a544391f733eca922fdcb326d19e894789cd4ff61d48b4b195776476c5cf",
                "sha256:f5fdf935a46aa20aa937f2478480ebf4be9186e98e49cc3843af9a5795a49a25"
            ],
            "index": "pypi",
            "version": "==0.800"
        },
        "mypy-extensions": {
            "hashes": [
                "sha256:090fedd75945a69ae91ce1303b5824f428daf5a028d2f6ab8a299250a846f15d",
                "sha256:2d82818f5bb3e369420cb3c4060a7970edba416647068eb4c5343488a6c604a8"
            ],
            "version": "==0.4.3"
        },
        "object-colors": {
            "hashes": [
                "sha256:8573351c9ca383aacce01f77cdb8b770a828b3f1a9b23ff9952c128c7b5cd0a3",
                "sha256:ef42b6276f1a1124e5c55b59e603ff82bfe63a888e14e9787c90f6d7ac47737b"
            ],
            "index": "pypi",
            "version": "==1.0.8"
        },
        "packaging": {
            "hashes": [
                "sha256:24e0da08660a87484d1602c30bb4902d74816b6985b93de36926f5bc95741858",
                "sha256:78598185a7008a470d64526a8059de9aaa449238f280fc9eb6b13ba6c4109093"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==20.8"
        },
        "pathspec": {
            "hashes": [
                "sha256:86379d6b86d75816baba717e64b1a3a3469deb93bb76d613c9ce79edc5cb68fd",
                "sha256:aa0cb481c4041bf52ffa7b0d8fa6cd3e88a2ca4879c533c9153882ee2556790d"
            ],
            "version": "==0.8.1"
        },
        "pipfile-requirements": {
            "hashes": [
                "sha256:d47591d46d8bfecf9257967992feae31fa83aff7ab6417373c7de5ea92ab849f",
                "sha256:dc2ff7515ce35f8b37a500e87e7b9cd39f0f5c18eb6024543366eb6d4226869b"
            ],
            "index": "pypi",
            "version": "==0.3.0"
        },
        "pluggy": {
            "hashes": [
                "sha256:15b2acde666561e1298d71b523007ed7364de07029219b604cf808bfa1c765b0",
                "sha256:966c145cd83c96502c3c3868f50408687b38434af77734af1e9ca461a4081d2d"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==0.13.1"
        },
        "py": {
            "hashes": [
                "sha256:21b81bda15b66ef5e1a777a21c4dcd9c20ad3efd0b3f817e7a809035269e1bd3",
                "sha256:3b80836aa6d1feeaa108e046da6423ab8f6ceda6468545ae8d02d9d58d18818a"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.10.0"
        },
        "pyblake2": {
            "hashes": [
                "sha256:3757f7ad709b0e1b2a6b3919fa79fe3261f166fc375cd521f2be480f8319dde9",
                "sha256:407e02c7f8f36fcec1b7aa114ddca0c1060c598142ea6f6759d03710b946a7e3",
                "sha256:4d47b4a2c1d292b1e460bde1dda4d13aa792ed2ed70fcc263b6bc24632c8e902",
                "sha256:5ccc7eb02edb82fafb8adbb90746af71460fbc29aa0f822526fc976dff83e93f",
                "sha256:8043267fbc0b2f3748c6920591cd0b8b5609dcce60c504c32858aa36206386f2",
                "sha256:982295a87907d50f4723db6bc724660da76b6547826d52160171d54f95b919ac",
                "sha256:baa2190bfe549e36163aa44664d4ee3a9080b236fc5d42f50dc6fd36bbdc749e",
                "sha256:c53417ee0bbe77db852d5fd1036749f03696ebc2265de359fe17418d800196c4",
                "sha256:fbc9fcde75713930bc2a91b149e97be2401f7c9c56d735b46a109210f58d7358"
            ],
            "index": "pypi",
            "version": "==1.1.2"
        },
        "pygments": {
            "hashes": [
                "sha256:bc9591213a8f0e0ca1a5e68a479b4887fdc3e75d0774e5c71c31920c427de435",
                "sha256:df49d09b498e83c1a73128295860250b0b7edd4c723a32e9bc0d295c7c2ec337"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==2.7.4"
        },
        "pylint": {
            "hashes": [
                "sha256:bb4a908c9dadbc3aac18860550e870f58e1a02c9f2c204fdf5693d73be061210",
                "sha256:bfe68f020f8a0fece830a22dd4d5dddb4ecc6137db04face4c3420a46a52239f"
            ],
            "index": "pypi",
            "version": "==2.6.0"
        },
        "pyparsing": {
            "hashes": [
                "sha256:c203ec8783bf771a155b207279b9bccb8dea02d8f0c9e5f8ead507bc3246ecc1",
                "sha256:ef9d7589ef3c200abe66653d3f1ab1033c3c419ae9b9bdb1240a85b024efc88b"
            ],
            "markers": "python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==2.4.7"
        },
        "pytest": {
            "hashes": [
                "sha256:1969f797a1a0dbd8ccf0fecc80262312729afea9c17f1d70ebf85c5e76c6f7c8",
                "sha256:66e419b1899bc27346cb2c993e12c5e5e8daba9073c1fbce33b9807abc95c306"
            ],
            "index": "pypi",
            "version": "==6.2.1"
        },
        "pytest-cov": {
            "hashes": [
                "sha256:359952d9d39b9f822d9d29324483e7ba04a3a17dd7d05aa6beb7ea01e359e5f7",
                "sha256:bdb9fdb0b85a7cc825269a4c56b48ccaa5c7e365054b6038772c32ddcdc969da"
            ],
            "index": "pypi",
            "version": "==2.11.1"
        },
        "pytest-profiling": {
            "hashes": [
                "sha256:3b255f9db36cb2dd7536a8e7e294c612c0be7f7850a7d30754878e4315d56600",
                "sha256:6bce4e2edc04409d2f3158c16750fab8074f62d404cc38eeb075dff7fcbb996c",
                "sha256:93938f147662225d2b8bd5af89587b979652426a8a6ffd7e73ec4a23e24b7f29",
                "sha256:999cc9ac94f2e528e3f5d43465da277429984a1c237ae9818f8cfd0b06acb019"
            ],
            "index": "pypi",
            "version": "==1.7.0"
        },
        "pytest-randomly": {
            "hashes": [
                "sha256:440cec143fd9b0adeb072006c71e0294402a2bc2ccd08079c2341087ba4cf2d1",
                "sha256:9db10d160237f3f8ee60cef72e4cb9ea88d2893c9dd5c8aa334b060cdeb67c3a"
            ],
            "index": "pypi",
            "version": "==3.5.0"
        },
        "pytest-sugar": {
            "hashes": [
                "sha256:b1b2186b0a72aada6859bea2a5764145e3aaa2c1cfbb23c3a19b5f7b697563d3"
            ],
            "index": "pypi",
            "version": "==0.9.4"
        },
        "pytz": {
            "hashes": [
                "sha256:16962c5fb8db4a8f63a26646d8886e9d769b6c511543557bc84e9569fb9a9cb4",
                "sha256:180befebb1927b16f6b57101720075a984c019ac16b1b7575673bea42c6c3da5"
            ],
            "version": "==2020.5"
        },
        "regex": {
            "hashes": [
                "sha256:02951b7dacb123d8ea6da44fe45ddd084aa6777d4b2454fa0da61d569c6fa538",
                "sha256:0d08e71e70c0237883d0bef12cad5145b84c3705e9c6a588b2a9c7080e5af2a4",
                "sha256:1862a9d9194fae76a7aaf0150d5f2a8ec1da89e8b55890b1786b8f88a0f619dc",
                "sha256:1ab79fcb02b930de09c76d024d279686ec5d532eb814fd0ed1e0051eb8bd2daa",
                "sha256:1fa7ee9c2a0e30405e21031d07d7ba8617bc590d391adfc2b7f1e8b99f46f444",
                "sha256:262c6825b309e6485ec2493ffc7e62a13cf13fb2a8b6d212f72bd53ad34118f1",
                "sha256:2a11a3e90bd9901d70a5b31d7dd85114755a581a5da3fc996abfefa48aee78af",
                "sha256:2c99e97d388cd0a8d30f7c514d67887d8021541b875baf09791a3baad48bb4f8",
                "sha256:3128e30d83f2e70b0bed9b2a34e92707d0877e460b402faca908c6667092ada9",
                "sha256:38c8fd190db64f513fe4e1baa59fed086ae71fa45083b6936b52d34df8f86a88",
                "sha256:3bddc701bdd1efa0d5264d2649588cbfda549b2899dc8d50417e47a82e1387ba",
                "sha256:4902e6aa086cbb224241adbc2f06235927d5cdacffb2425c73e6570e8d862364",
                "sha256:49cae022fa13f09be91b2c880e58e14b6da5d10639ed45ca69b85faf039f7a4e",
                "sha256:56e01daca75eae420bce184edd8bb341c8eebb19dd3bce7266332258f9fb9dd7",
                "sha256:5862975b45d451b6db51c2e654990c1820523a5b07100fc6903e9c86575202a0",
                "sha256:6a8ce43923c518c24a2579fda49f093f1397dad5d18346211e46f134fc624e31",
                "sha256:6c54ce4b5d61a7129bad5c5dc279e222afd00e721bf92f9ef09e4fae28755683",
                "sha256:6e4b08c6f8daca7d8f07c8d24e4331ae7953333dbd09c648ed6ebd24db5a10ee",
                "sha256:717881211f46de3ab130b58ec0908267961fadc06e44f974466d1887f865bd5b",
                "sha256:749078d1eb89484db5f34b4012092ad14b327944ee7f1c4f74d6279a6e4d1884",
                "sha256:7913bd25f4ab274ba37bc97ad0e21c31004224ccb02765ad984eef43e04acc6c",
                "sha256:7a25fcbeae08f96a754b45bdc050e1fb94b95cab046bf56b016c25e9ab127b3e",
                "sha256:83d6b356e116ca119db8e7c6fc2983289d87b27b3fac238cfe5dca529d884562",
                "sha256:8b882a78c320478b12ff024e81dc7d43c1462aa4a3341c754ee65d857a521f85",
                "sha256:8f6a2229e8ad946e36815f2a03386bb8353d4bde368fdf8ca5f0cb97264d3b5c",
                "sha256:9801c4c1d9ae6a70aeb2128e5b4b68c45d4f0af0d1535500884d644fa9b768c6",
                "sha256:a15f64ae3a027b64496a71ab1f722355e570c3fac5ba2801cafce846bf5af01d",
                "sha256:a3d748383762e56337c39ab35c6ed4deb88df5326f97a38946ddd19028ecce6b",
                "sha256:a63f1a07932c9686d2d416fb295ec2c01ab246e89b4d58e5fa468089cab44b70",
                "sha256:b2b1a5ddae3677d89b686e5c625fc5547c6e492bd755b520de5332773a8af06b",
                "sha256:b2f4007bff007c96a173e24dcda236e5e83bde4358a557f9ccf5e014439eae4b",
                "sha256:baf378ba6151f6e272824b86a774326f692bc2ef4cc5ce8d5bc76e38c813a55f",
                "sha256:bafb01b4688833e099d79e7efd23f99172f501a15c44f21ea2118681473fdba0",
                "sha256:bba349276b126947b014e50ab3316c027cac1495992f10e5682dc677b3dfa0c5",
                "sha256:c084582d4215593f2f1d28b65d2a2f3aceff8342aa85afd7be23a9cad74a0de5",
                "sha256:d1ebb090a426db66dd80df8ca85adc4abfcbad8a7c2e9a5ec7513ede522e0a8f",
                "sha256:d2d8ce12b7c12c87e41123997ebaf1a5767a5be3ec545f64675388970f415e2e",
                "sha256:e32f5f3d1b1c663af7f9c4c1e72e6ffe9a78c03a31e149259f531e0fed826512",
                "sha256:e3faaf10a0d1e8e23a9b51d1900b72e1635c2d5b0e1bea1c18022486a8e2e52d",
                "sha256:f7d29a6fc4760300f86ae329e3b6ca28ea9c20823df123a2ea8693e967b29917",
                "sha256:f8f295db00ef5f8bae530fc39af0b40486ca6068733fb860b42115052206466f"
            ],
            "version": "==2020.11.13"
        },
        "requests": {
            "hashes": [
                "sha256:27973dd4a904a4f13b263a19c866c13b92a39ed1c964655f025f3f8d3d75b804",
                "sha256:c210084e36a42ae6b9219e00e48287def368a26d03a048ddad7bfee44f75871e"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==2.25.1"
        },
        "six": {
            "hashes": [
                "sha256:30639c035cdb23534cd4aa2dd52c3bf48f06e5f4a941509c8bafd8ce11080259",
                "sha256:8b74bedcbbbaca38ff6d7491d76f2b06b3592611af620f8426e82dddb04a5ced"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.15.0"
        },
        "snowballstemmer": {
            "hashes": [
                "sha256:b51b447bea85f9968c13b650126a888aabd4cb4463fca868ec596826325dedc2",
                "sha256:e997baa4f2e9139951b6f4c631bad912dfd3c792467e2f03d7239464af90e914"
            ],
            "version": "==2.1.0"
        },
        "sphinx": {
            "hashes": [
                "sha256:41cad293f954f7d37f803d97eb184158cfd90f51195131e94875bc07cd08b93c",
                "sha256:c314c857e7cd47c856d2c5adff514ac2e6495f8b8e0f886a8a37e9305dfea0d8"
            ],
            "index": "pypi",
            "version": "==3.4.3"
        },
        "sphinxcontrib-applehelp": {
            "hashes": [
                "sha256:806111e5e962be97c29ec4c1e7fe277bfd19e9652fb1a4392105b43e01af885a",
                "sha256:a072735ec80e7675e3f432fcae8610ecf509c5f1869d17e2eecff44389cdbc58"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.2"
        },
        "sphinxcontrib-devhelp": {
            "hashes": [
                "sha256:8165223f9a335cc1af7ffe1ed31d2871f325254c0423bc0c4c7cd1c1e4734a2e",
                "sha256:ff7f1afa7b9642e7060379360a67e9c41e8f3121f2ce9164266f61b9f4b338e4"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.2"
        },
        "sphinxcontrib-fulltoc": {
            "hashes": [
                "sha256:c845d62fc467f3135d4543e9f10e13ef91852683bd1c90fd19d07f9d36757cd9"
            ],
            "index": "pypi",
            "version": "==1.2.0"
        },
        "sphinxcontrib-htmlhelp": {
            "hashes": [
                "sha256:3c0bc24a2c41e340ac37c85ced6dafc879ab485c095b1d65d2461ac2f7cca86f",
                "sha256:e8f5bb7e31b2dbb25b9cc435c8ab7a79787ebf7f906155729338f3156d93659b"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.3"
        },
        "sphinxcontrib-jsmath": {
            "hashes": [
                "sha256:2ec2eaebfb78f3f2078e73666b1415417a116cc848b72e5172e596c871103178",
                "sha256:a9925e4a4587247ed2191a22df5f6970656cb8ca2bd6284309578f2153e0c4b8"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.1"
        },
        "sphinxcontrib-programoutput": {
            "hashes": [
                "sha256:0caaa216d0ad8d2cfa90a9a9dba76820e376da6e3152be28d10aedc09f82a3b0",
                "sha256:8009d1326b89cd029ee477ce32b45c58d92b8504d48811461c3117014a8f4b1e"
            ],
            "index": "pypi",
            "version": "==0.16"
        },
        "sphinxcontrib-qthelp": {
            "hashes": [
                "sha256:4c33767ee058b70dba89a6fc5c1892c0d57a54be67ddd3e7875a18d14cba5a72",
                "sha256:bd9fc24bcb748a8d51fd4ecaade681350aa63009a347a8c14e637895444dfab6"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.3"
        },
        "sphinxcontrib-serializinghtml": {
            "hashes": [
                "sha256:eaa0eccc86e982a9b939b2b82d12cc5d013385ba5eadcc7e4fed23f4405f77bc",
                "sha256:f242a81d423f59617a8e5cf16f5d4d74e28ee9a66f9e5b637a18082991db5a9a"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.1.4"
        },
        "termcolor": {
            "hashes": [
                "sha256:1d6d69ce66211143803fbc56652b41d73b4a400a2891d7bf7a1cdf4c02de613b"
            ],
            "version": "==1.1.0"
        },
        "toml": {
            "hashes": [
                "sha256:806143ae5bfb6a3c6e736a764057db0e6a0e05e338b5630894a5f779cabb4f9b",
                "sha256:b3bda1d108d5dd99f4a20d24d9c348e91c4db7ab1b749200bded2f839ccbe68f"
            ],
            "markers": "python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==0.10.2"
        },
        "typed-ast": {
            "hashes": [
                "sha256:07d49388d5bf7e863f7fa2f124b1b1d89d8aa0e2f7812faff0a5658c01c59aa1",
                "sha256:14bf1522cdee369e8f5581238edac09150c765ec1cb33615855889cf33dcb92d",
                "sha256:240296b27397e4e37874abb1df2a608a92df85cf3e2a04d0d4d61055c8305ba6",
                "sha256:36d829b31ab67d6fcb30e185ec996e1f72b892255a745d3a82138c97d21ed1cd",
                "sha256:37f48d46d733d57cc70fd5f30572d11ab8ed92da6e6b28e024e4a3edfb456e37",
                "sha256:4c790331247081ea7c632a76d5b2a265e6d325ecd3179d06e9cf8d46d90dd151",
                "sha256:5dcfc2e264bd8a1db8b11a892bd1647154ce03eeba94b461effe68790d8b8e07",
                "sha256:7147e2a76c75f0f64c4319886e7639e490fee87c9d25cb1d4faef1d8cf83a440",
                "sha256:7703620125e4fb79b64aa52427ec192822e9f45d37d4b6625ab37ef403e1df70",
                "sha256:8368f83e93c7156ccd40e49a783a6a6850ca25b556c0fa0240ed0f659d2fe496",
                "sha256:84aa6223d71012c68d577c83f4e7db50d11d6b1399a9c779046d75e24bed74ea",
                "sha256:85f95aa97a35bdb2f2f7d10ec5bbdac0aeb9dafdaf88e17492da0504de2e6400",
                "sha256:8db0e856712f79c45956da0c9a40ca4246abc3485ae0d7ecc86a20f5e4c09abc",
                "sha256:9044ef2df88d7f33692ae3f18d3be63dec69c4fb1b5a4a9ac950f9b4ba571606",
                "sha256:963c80b583b0661918718b095e02303d8078950b26cc00b5e5ea9ababe0de1fc",
                "sha256:987f15737aba2ab5f3928c617ccf1ce412e2e321c77ab16ca5a293e7bbffd581",
                "sha256:9ec45db0c766f196ae629e509f059ff05fc3148f9ffd28f3cfe75d4afb485412",
                "sha256:9fc0b3cb5d1720e7141d103cf4819aea239f7d136acf9ee4a69b047b7986175a",
                "sha256:a2c927c49f2029291fbabd673d51a2180038f8cd5a5b2f290f78c4516be48be2",
                "sha256:a38878a223bdd37c9709d07cd357bb79f4c760b29210e14ad0fb395294583787",
                "sha256:b4fcdcfa302538f70929eb7b392f536a237cbe2ed9cba88e3bf5027b39f5f77f",
                "sha256:c0c74e5579af4b977c8b932f40a5464764b2f86681327410aa028a22d2f54937",
                "sha256:c1c876fd795b36126f773db9cbb393f19808edd2637e00fd6caba0e25f2c7b64",
                "sha256:c9aadc4924d4b5799112837b226160428524a9a45f830e0d0f184b19e4090487",
                "sha256:cc7b98bf58167b7f2db91a4327da24fb93368838eb84a44c472283778fc2446b",
                "sha256:cf54cfa843f297991b7388c281cb3855d911137223c6b6d2dd82a47ae5125a41",
                "sha256:d003156bb6a59cda9050e983441b7fa2487f7800d76bdc065566b7d728b4581a",
                "sha256:d175297e9533d8d37437abc14e8a83cbc68af93cc9c1c59c2c292ec59a0697a3",
                "sha256:d746a437cdbca200622385305aedd9aef68e8a645e385cc483bdc5e488f07166",
                "sha256:e683e409e5c45d5c9082dc1daf13f6374300806240719f95dc783d1fc942af10"
            ],
            "version": "==1.4.2"
        },
        "typing-extensions": {
            "hashes": [
                "sha256:7cb407020f00f7bfc3cb3e7881628838e69d8f3fcab2f64742a5e76b2f841918",
                "sha256:99d4073b617d30288f569d3f13d2bd7548c3a7e4c8de87db09a9d29bb3a4a60c",
                "sha256:dafc7639cde7f1b6e1acc0f457842a83e722ccca8eef5270af2d74792619a89f"
            ],
            "version": "==3.7.4.3"
        },
        "urllib3": {
            "hashes": [
                "sha256:19188f96923873c92ccb987120ec4acaa12f0461fa9ce5d3d0772bc965a39e08",
                "sha256:d8ff90d979214d7b4f8ce956e80f4028fc6860e4431f731ea4a8c08f23f99473"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4' and python_version < '4.0'",
            "version": "==1.26.2"
        },
        "vulture": {
            "hashes": [
                "sha256:03d5a62bcbe9ceb9a9b0575f42d71a2d414070229f2e6f95fa6e7c71aaaed967",
                "sha256:f39de5e6f1df1f70c3b50da54f1c8d494159e9ca3d01a9b89eac929600591703"
            ],
            "index": "pypi",
            "version": "==2.3"
        },
        "wrapt": {
            "hashes": [
                "sha256:b62ffa81fb85f4332a4f609cab4ac40709470da05643a082ec1eb88e6d9b97d7"
            ],
            "version": "==1.12.1"
        }
    },
    "develop": {
        "alabaster": {
            "hashes": [
                "sha256:446438bdcca0e05bd45ea2de1668c1d9b032e1a9154c2c259092d77031ddd359",
                "sha256:a661d72d58e6ea8a57f7a86e37d86716863ee5e92788398526d58b26a4e4dc02"
            ],
            "version": "==0.7.12"
        },
        "appdirs": {
            "hashes": [
                "sha256:7d5d0167b2b1ba821647616af46a749d1c653740dd0d2415100fe26e27afdf41",
                "sha256:a841dacd6b99318a741b166adb07e19ee71a274450e68237b4650ca1055ab128"
            ],
            "index": "pypi",
            "version": "==1.4.4"
        },
        "astroid": {
            "hashes": [
                "sha256:2f4078c2a41bf377eea06d71c9d2ba4eb8f6b1af2135bec27bbbb7d8f12bb703",
                "sha256:bc58d83eb610252fd8de6363e39d4f1d0619c894b0ed24603b881c02e64c7386"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==2.4.2"
        },
        "attrs": {
            "hashes": [
                "sha256:31b2eced602aa8423c2aea9c76a724617ed67cf9513173fd3a4f03e3a929c7e6",
                "sha256:832aa3cde19744e49938b91fea06d69ecb9e649c93ba974535d08ad92164f700"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==20.3.0"
        },
        "babel": {
            "hashes": [
                "sha256:9d35c22fcc79893c3ecc85ac4a56cde1ecf3f19c540bba0922308a6c06ca6fa5",
                "sha256:da031ab54472314f210b0adcff1588ee5d1d1d0ba4dbd07b94dba82bde791e05"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==2.9.0"
        },
        "backcall": {
            "hashes": [
                "sha256:5cbdbf27be5e7cfadb448baf0aa95508f91f2bbc6c6437cd9cd06e2a4c215e1e",
                "sha256:fbbce6a29f263178a1f7915c1940bde0ec2b2a967566fe1c65c1dfb7422bd255"
            ],
            "version": "==0.2.0"
        },
        "black": {
            "hashes": [
                "sha256:1c02557aa099101b9d21496f8a914e9ed2222ef70336404eeeac8edba836fbea"
            ],
            "index": "pypi",
            "version": "==20.8b1"
        },
        "bleach": {
            "hashes": [
                "sha256:a690ccc41a10d806a7c0a9130767750925e4863e332f7e4ea93da1bc12a24300",
                "sha256:ce6270dd0ae56cd810495b8d994551ae16b41f2b4043cf50064f298985afdb3c"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==3.2.2"
        },
        "certifi": {
            "hashes": [
                "sha256:1a4995114262bffbc2413b159f2a1a480c969de6e6eb13ee966d470af86af59c",
                "sha256:719a74fb9e33b9bd44cc7f3a8d94bc35e4049deebe19ba7d8e108280cfd59830"
            ],
            "version": "==2020.12.5"
        },
        "chardet": {
            "hashes": [
                "sha256:0d6f53a15db4120f2b08c94f11e7d93d2c911ee118b6b30a04ec3ee8310179fa",
                "sha256:f864054d66fd9118f2e67044ac8981a54775ec5b67aed0441892edb553d21da5"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==4.0.0"
        },
        "click": {
            "hashes": [
                "sha256:d2b5255c7c6349bc1bd1e59e08cd12acbbd63ce649f2588755783aa94dfb6b1a",
                "sha256:dacca89f4bfadd5de3d7489b7c8a566eee0d3676333fbb50030263894c38c0dc"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==7.1.2"
        },
        "codecov": {
            "hashes": [
                "sha256:6cde272454009d27355f9434f4e49f238c0273b216beda8472a65dc4957f473b",
                "sha256:ba8553a82942ce37d4da92b70ffd6d54cf635fc1793ab0a7dc3fecd6ebfb3df8",
                "sha256:e95901d4350e99fc39c8353efa450050d2446c55bac91d90fcfd2354e19a6aef"
            ],
            "index": "pypi",
            "version": "==2.1.11"
        },
        "coverage": {
            "extras": [
                "toml"
            ],
            "hashes": [
                "sha256:08b3ba72bd981531fd557f67beee376d6700fba183b167857038997ba30dd297",
                "sha256:2757fa64e11ec12220968f65d086b7a29b6583d16e9a544c889b22ba98555ef1",
                "sha256:3102bb2c206700a7d28181dbe04d66b30780cde1d1c02c5f3c165cf3d2489497",
                "sha256:3498b27d8236057def41de3585f317abae235dd3a11d33e01736ffedb2ef8606",
                "sha256:378ac77af41350a8c6b8801a66021b52da8a05fd77e578b7380e876c0ce4f528",
                "sha256:38f16b1317b8dd82df67ed5daa5f5e7c959e46579840d77a67a4ceb9cef0a50b",
                "sha256:3911c2ef96e5ddc748a3c8b4702c61986628bb719b8378bf1e4a6184bbd48fe4",
                "sha256:3a3c3f8863255f3c31db3889f8055989527173ef6192a283eb6f4db3c579d830",
                "sha256:3b14b1da110ea50c8bcbadc3b82c3933974dbeea1832e814aab93ca1163cd4c1",
                "sha256:535dc1e6e68fad5355f9984d5637c33badbdc987b0c0d303ee95a6c979c9516f",
                "sha256:6f61319e33222591f885c598e3e24f6a4be3533c1d70c19e0dc59e83a71ce27d",
                "sha256:723d22d324e7997a651478e9c5a3120a0ecbc9a7e94071f7e1954562a8806cf3",
                "sha256:76b2775dda7e78680d688daabcb485dc87cf5e3184a0b3e012e1d40e38527cc8",
                "sha256:782a5c7df9f91979a7a21792e09b34a658058896628217ae6362088b123c8500",
                "sha256:7e4d159021c2029b958b2363abec4a11db0ce8cd43abb0d9ce44284cb97217e7",
                "sha256:8dacc4073c359f40fcf73aede8428c35f84639baad7e1b46fce5ab7a8a7be4bb",
                "sha256:8f33d1156241c43755137288dea619105477961cfa7e47f48dbf96bc2c30720b",
                "sha256:8ffd4b204d7de77b5dd558cdff986a8274796a1e57813ed005b33fd97e29f059",
                "sha256:93a280c9eb736a0dcca19296f3c30c720cb41a71b1f9e617f341f0a8e791a69b",
                "sha256:9a4f66259bdd6964d8cf26142733c81fb562252db74ea367d9beb4f815478e72",
                "sha256:9a9d4ff06804920388aab69c5ea8a77525cf165356db70131616acd269e19b36",
                "sha256:a2070c5affdb3a5e751f24208c5c4f3d5f008fa04d28731416e023c93b275277",
                "sha256:a4857f7e2bc6921dbd487c5c88b84f5633de3e7d416c4dc0bb70256775551a6c",
                "sha256:a607ae05b6c96057ba86c811d9c43423f35e03874ffb03fbdcd45e0637e8b631",
                "sha256:a66ca3bdf21c653e47f726ca57f46ba7fc1f260ad99ba783acc3e58e3ebdb9ff",
                "sha256:ab110c48bc3d97b4d19af41865e14531f300b482da21783fdaacd159251890e8",
                "sha256:b239711e774c8eb910e9b1ac719f02f5ae4bf35fa0420f438cdc3a7e4e7dd6ec",
                "sha256:be0416074d7f253865bb67630cf7210cbc14eb05f4099cc0f82430135aaa7a3b",
                "sha256:c46643970dff9f5c976c6512fd35768c4a3819f01f61169d8cdac3f9290903b7",
                "sha256:c5ec71fd4a43b6d84ddb88c1df94572479d9a26ef3f150cef3dacefecf888105",
                "sha256:c6e5174f8ca585755988bc278c8bb5d02d9dc2e971591ef4a1baabdf2d99589b",
                "sha256:c89b558f8a9a5a6f2cfc923c304d49f0ce629c3bd85cb442ca258ec20366394c",
                "sha256:cc44e3545d908ecf3e5773266c487ad1877be718d9dc65fc7eb6e7d14960985b",
                "sha256:cc6f8246e74dd210d7e2b56c76ceaba1cc52b025cd75dbe96eb48791e0250e98",
                "sha256:cd556c79ad665faeae28020a0ab3bda6cd47d94bec48e36970719b0b86e4dcf4",
                "sha256:ce6f3a147b4b1a8b09aae48517ae91139b1b010c5f36423fa2b866a8b23df879",
                "sha256:ceb499d2b3d1d7b7ba23abe8bf26df5f06ba8c71127f188333dddcf356b4b63f",
                "sha256:cef06fb382557f66d81d804230c11ab292d94b840b3cb7bf4450778377b592f4",
                "sha256:e448f56cfeae7b1b3b5bcd99bb377cde7c4eb1970a525c770720a352bc4c8044",
                "sha256:e52d3d95df81c8f6b2a1685aabffadf2d2d9ad97203a40f8d61e51b70f191e4e",
                "sha256:ee2f1d1c223c3d2c24e3afbb2dd38be3f03b1a8d6a83ee3d9eb8c36a52bee899",
                "sha256:f2c6888eada180814b8583c3e793f3f343a692fc802546eed45f40a001b1169f",
                "sha256:f51dbba78d68a44e99d484ca8c8f604f17e957c1ca09c3ebc2c7e3bbd9ba0448",
                "sha256:f54de00baf200b4539a5a092a759f000b5f45fd226d6d25a76b0dff71177a714",
                "sha256:fa10fee7e32213f5c7b0d6428ea92e3a3fdd6d725590238a3f92c0de1c78b9d2",
                "sha256:fabeeb121735d47d8eab8671b6b031ce08514c86b7ad8f7d5490a7b6dcd6267d",
                "sha256:fac3c432851038b3e6afe086f777732bcf7f6ebbfd90951fa04ee53db6d0bcdd",
                "sha256:fda29412a66099af6d6de0baa6bd7c52674de177ec2ad2630ca264142d69c6c7",
                "sha256:ff1330e8bc996570221b450e2d539134baa9465f5cb98aff0e0f73f34172e0ae"
            ],
            "index": "pypi",
            "version": "==5.3.1"
        },
        "decorator": {
            "hashes": [
                "sha256:41fa54c2a0cc4ba648be4fd43cff00aedf5b9465c9bf18d64325bc225f08f760",
                "sha256:e3a62f0520172440ca0dcc823749319382e377f37f140a0b99ef45fecb84bfe7"
            ],
            "version": "==4.4.2"
        },
        "docutils": {
            "hashes": [
                "sha256:0c5b78adfbf7762415433f5515cd5c9e762339e23369dbe8000d84a4bf4ab3af",
                "sha256:c2de3a60e9e7d07be26b7f2b00ca0309c207e06c100f9cc2a94931fc75a478fc"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==0.16"
        },
        "idna": {
            "hashes": [
                "sha256:b307872f855b18632ce0c21c5e45be78c0ea7ae4c15c828c20788b26921eb3f6",
                "sha256:b97d804b1e9b523befed77c48dacec60e6dcb0b5391d57af6a65a312a90648c0"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==2.10"
        },
        "imagesize": {
            "hashes": [
                "sha256:6965f19a6a2039c7d48bca7dba2473069ff854c36ae6f19d2cde309d998228a1",
                "sha256:b1f6b5a4eab1f73479a50fb79fcf729514a900c341d8503d62a62dbc4127a2b1"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.2.0"
        },
        "iniconfig": {
            "hashes": [
                "sha256:011e24c64b7f47f6ebd835bb12a743f2fbe9a26d4cecaa7f53bc4f35ee9da8b3",
                "sha256:bc3af051d7d14b2ee5ef9969666def0cd1a000e121eaea580d4a313df4b37f32"
            ],
            "version": "==1.1.1"
        },
        "ipython": {
            "hashes": [
                "sha256:c987e8178ced651532b3b1ff9965925bfd445c279239697052561a9ab806d28f",
                "sha256:cbb2ef3d5961d44e6a963b9817d4ea4e1fa2eb589c371a470fed14d8d40cbd6a"
            ],
            "index": "pypi",
            "version": "==7.19.0"
        },
        "ipython-genutils": {
            "hashes": [
                "sha256:72dd37233799e619666c9f639a9da83c34013a73e8bbc79a7a6348d93c61fab8",
                "sha256:eb2e116e75ecef9d4d228fdc66af54269afa26ab4463042e33785b887c628ba8"
            ],
            "version": "==0.2.0"
        },
        "isort": {
            "hashes": [
                "sha256:c729845434366216d320e936b8ad6f9d681aab72dc7cbc2d51bedc3582f3ad1e",
                "sha256:fff4f0c04e1825522ce6949973e83110a6e907750cd92d128b0d14aaaadbffdc"
            ],
            "markers": "python_version >= '3.6' and python_version < '4.0'",
            "version": "==5.7.0"
        },
        "jedi": {
            "hashes": [
                "sha256:18456d83f65f400ab0c2d3319e48520420ef43b23a086fdc05dff34132f0fb93",
                "sha256:92550a404bad8afed881a137ec9a461fed49eca661414be45059329614ed0707"
            ],
            "markers": "python_version >= '3.6'",
            "version": "==0.18.0"
        },
        "jinja2": {
            "hashes": [
                "sha256:89aab215427ef59c34ad58735269eb58b1a5808103067f7bb9d5836c651b3bb0",
                "sha256:f0a4641d3cf955324a89c04f3d94663aa4d638abe8f733ecd3582848e1c37035"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==2.11.2"
        },
        "lazy-object-proxy": {
            "hashes": [
                "sha256:0c4b206227a8097f05c4dbdd323c50edf81f15db3b8dc064d08c62d37e1a504d",
                "sha256:194d092e6f246b906e8f70884e620e459fc54db3259e60cf69a4d66c3fda3449",
                "sha256:1be7e4c9f96948003609aa6c974ae59830a6baecc5376c25c92d7d697e684c08",
                "sha256:4677f594e474c91da97f489fea5b7daa17b5517190899cf213697e48d3902f5a",
                "sha256:48dab84ebd4831077b150572aec802f303117c8cc5c871e182447281ebf3ac50",
                "sha256:5541cada25cd173702dbd99f8e22434105456314462326f06dba3e180f203dfd",
                "sha256:59f79fef100b09564bc2df42ea2d8d21a64fdcda64979c0fa3db7bdaabaf6239",
                "sha256:8d859b89baf8ef7f8bc6b00aa20316483d67f0b1cbf422f5b4dc56701c8f2ffb",
                "sha256:9254f4358b9b541e3441b007a0ea0764b9d056afdeafc1a5569eee1cc6c1b9ea",
                "sha256:9651375199045a358eb6741df3e02a651e0330be090b3bc79f6d0de31a80ec3e",
                "sha256:97bb5884f6f1cdce0099f86b907aa41c970c3c672ac8b9c8352789e103cf3156",
                "sha256:9b15f3f4c0f35727d3a0fba4b770b3c4ebbb1fa907dbcc046a1d2799f3edd142",
                "sha256:a2238e9d1bb71a56cd710611a1614d1194dc10a175c1e08d75e1a7bcc250d442",
                "sha256:a6ae12d08c0bf9909ce12385803a543bfe99b95fe01e752536a60af2b7797c62",
                "sha256:ca0a928a3ddbc5725be2dd1cf895ec0a254798915fb3a36af0964a0a4149e3db",
                "sha256:cb2c7c57005a6804ab66f106ceb8482da55f5314b7fcb06551db1edae4ad1531",
                "sha256:d74bb8693bf9cf75ac3b47a54d716bbb1a92648d5f781fc799347cfc95952383",
                "sha256:d945239a5639b3ff35b70a88c5f2f491913eb94871780ebfabb2568bd58afc5a",
                "sha256:eba7011090323c1dadf18b3b689845fd96a61ba0a1dfbd7f24b921398affc357",
                "sha256:efa1909120ce98bbb3777e8b6f92237f5d5c8ea6758efea36a473e1d38f7d3e4",
                "sha256:f3900e8a5de27447acbf900b4750b0ddfd7ec1ea7fbaf11dfa911141bc522af0"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.4.3"
        },
        "markupsafe": {
            "hashes": [
                "sha256:00bc623926325b26bb9605ae9eae8a215691f33cae5df11ca5424f06f2d1f473",
                "sha256:09027a7803a62ca78792ad89403b1b7a73a01c8cb65909cd876f7fcebd79b161",
                "sha256:09c4b7f37d6c648cb13f9230d847adf22f8171b1ccc4d5682398e77f40309235",
                "sha256:1027c282dad077d0bae18be6794e6b6b8c91d58ed8a8d89a89d59693b9131db5",
                "sha256:13d3144e1e340870b25e7b10b98d779608c02016d5184cfb9927a9f10c689f42",
                "sha256:24982cc2533820871eba85ba648cd53d8623687ff11cbb805be4ff7b4c971aff",
                "sha256:29872e92839765e546828bb7754a68c418d927cd064fd4708fab9fe9c8bb116b",
                "sha256:43a55c2930bbc139570ac2452adf3d70cdbb3cfe5912c71cdce1c2c6bbd9c5d1",
                "sha256:46c99d2de99945ec5cb54f23c8cd5689f6d7177305ebff350a58ce5f8de1669e",
                "sha256:500d4957e52ddc3351cabf489e79c91c17f6e0899158447047588650b5e69183",
                "sha256:535f6fc4d397c1563d08b88e485c3496cf5784e927af890fb3c3aac7f933ec66",
                "sha256:596510de112c685489095da617b5bcbbac7dd6384aeebeda4df6025d0256a81b",
                "sha256:62fe6c95e3ec8a7fad637b7f3d372c15ec1caa01ab47926cfdf7a75b40e0eac1",
                "sha256:6788b695d50a51edb699cb55e35487e430fa21f1ed838122d722e0ff0ac5ba15",
                "sha256:6dd73240d2af64df90aa7c4e7481e23825ea70af4b4922f8ede5b9e35f78a3b1",
                "sha256:717ba8fe3ae9cc0006d7c451f0bb265ee07739daf76355d06366154ee68d221e",
                "sha256:79855e1c5b8da654cf486b830bd42c06e8780cea587384cf6545b7d9ac013a0b",
                "sha256:7c1699dfe0cf8ff607dbdcc1e9b9af1755371f92a68f706051cc8c37d447c905",
                "sha256:88e5fcfb52ee7b911e8bb6d6aa2fd21fbecc674eadd44118a9cc3863f938e735",
                "sha256:8defac2f2ccd6805ebf65f5eeb132adcf2ab57aa11fdf4c0dd5169a004710e7d",
                "sha256:98c7086708b163d425c67c7a91bad6e466bb99d797aa64f965e9d25c12111a5e",
                "sha256:9add70b36c5666a2ed02b43b335fe19002ee5235efd4b8a89bfcf9005bebac0d",
                "sha256:9bf40443012702a1d2070043cb6291650a0841ece432556f784f004937f0f32c",
                "sha256:ade5e387d2ad0d7ebf59146cc00c8044acbd863725f887353a10df825fc8ae21",
                "sha256:b00c1de48212e4cc9603895652c5c410df699856a2853135b3967591e4beebc2",
                "sha256:b1282f8c00509d99fef04d8ba936b156d419be841854fe901d8ae224c59f0be5",
                "sha256:b2051432115498d3562c084a49bba65d97cf251f5a331c64a12ee7e04dacc51b",
                "sha256:ba59edeaa2fc6114428f1637ffff42da1e311e29382d81b339c1817d37ec93c6",
                "sha256:c8716a48d94b06bb3b2524c2b77e055fb313aeb4ea620c8dd03a105574ba704f",
                "sha256:cd5df75523866410809ca100dc9681e301e3c27567cf498077e8551b6d20e42f",
                "sha256:cdb132fc825c38e1aeec2c8aa9338310d29d337bebbd7baa06889d09a60a1fa2",
                "sha256:e249096428b3ae81b08327a63a485ad0878de3fb939049038579ac0ef61e17e7",
                "sha256:e8313f01ba26fbbe36c7be1966a7b7424942f670f38e666995b88d012765b9be"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.1.1"
        },
        "mccabe": {
            "hashes": [
                "sha256:ab8a6258860da4b6677da4bd2fe5dc2c659cff31b3ee4f7f5d64e79735b80d42",
                "sha256:dd8d182285a0fe56bace7f45b5e7d1a6ebcbf524e8f3bd87eb0f125271b8831f"
            ],
            "version": "==0.6.1"
        },
        "mypy": {
            "hashes": [
                "sha256:0d2fc8beb99cd88f2d7e20d69131353053fbecea17904ee6f0348759302c52fa",
                "sha256:2b216eacca0ec0ee124af9429bfd858d5619a0725ee5f88057e6e076f9eb1a7b",
                "sha256:319ee5c248a7c3f94477f92a729b7ab06bf8a6d04447ef3aa8c9ba2aa47c6dcf",
                "sha256:3e0c159a7853e3521e3f582adb1f3eac66d0b0639d434278e2867af3a8c62653",
                "sha256:5615785d3e2f4f03ab7697983d82c4b98af5c321614f51b8f1034eb9ebe48363",
                "sha256:5ff616787122774f510caeb7b980542a7cc2222be3f00837a304ea85cd56e488",
                "sha256:6f8425fecd2ba6007e526209bb985ce7f49ed0d2ac1cc1a44f243380a06a84fb",
                "sha256:74f5aa50d0866bc6fb8e213441c41e466c86678c800700b87b012ed11c0a13e0",
                "sha256:90b6f46dc2181d74f80617deca611925d7e63007cf416397358aa42efb593e07",
                "sha256:947126195bfe4709c360e89b40114c6746ae248f04d379dca6f6ab677aa07641",
                "sha256:a301da58d566aca05f8f449403c710c50a9860782148332322decf73a603280b",
                "sha256:aa9d4901f3ee1a986a3a79fe079ffbf7f999478c281376f48faa31daaa814e86",
                "sha256:b9150db14a48a8fa114189bfe49baccdff89da8c6639c2717750c7ae62316738",
                "sha256:b95068a3ce3b50332c40e31a955653be245666a4bc7819d3c8898aa9fb9ea496",
                "sha256:ca7ad5aed210841f1e77f5f2f7d725b62c78fa77519312042c719ed2ab937876",
                "sha256:d16c54b0dffb861dc6318a8730952265876d90c5101085a4bc56913e8521ba19",
                "sha256:e0202e37756ed09daf4b0ba64ad2c245d357659e014c3f51d8cd0681ba66940a",
                "sha256:e1c84c65ff6d69fb42958ece5b1255394714e0aac4df5ffe151bc4fe19c7600a",
                "sha256:e32b7b282c4ed4e378bba8b8dfa08e1cfa6f6574067ef22f86bee5b1039de0c9",
                "sha256:e3b8432f8df19e3c11235c4563a7250666dc9aa7cdda58d21b4177b20256ca9f",
                "sha256:e497a544391f733eca922fdcb326d19e894789cd4ff61d48b4b195776476c5cf",
                "sha256:f5fdf935a46aa20aa937f2478480ebf4be9186e98e49cc3843af9a5795a49a25"
            ],
            "index": "pypi",
            "version": "==0.800"
        },
        "mypy-extensions": {
            "hashes": [
                "sha256:090fedd75945a69ae91ce1303b5824f428daf5a028d2f6ab8a299250a846f15d",
                "sha256:2d82818f5bb3e369420cb3c4060a7970edba416647068eb4c5343488a6c604a8"
            ],
            "version": "==0.4.3"
        },
        "object-colors": {
            "hashes": [
                "sha256:8573351c9ca383aacce01f77cdb8b770a828b3f1a9b23ff9952c128c7b5cd0a3",
                "sha256:ef42b6276f1a1124e5c55b59e603ff82bfe63a888e14e9787c90f6d7ac47737b"
            ],
            "index": "pypi",
            "version": "==1.0.8"
        },
        "packaging": {
            "hashes": [
                "sha256:24e0da08660a87484d1602c30bb4902d74816b6985b93de36926f5bc95741858",
                "sha256:78598185a7008a470d64526a8059de9aaa449238f280fc9eb6b13ba6c4109093"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==20.8"
        },
        "parso": {
            "hashes": [
                "sha256:15b00182f472319383252c18d5913b69269590616c947747bc50bf4ac768f410",
                "sha256:8519430ad07087d4c997fda3a7918f7cfa27cb58972a8c89c2a0295a1c940e9e"
            ],
            "markers": "python_version >= '3.6'",
            "version": "==0.8.1"
        },
        "pathspec": {
            "hashes": [
                "sha256:86379d6b86d75816baba717e64b1a3a3469deb93bb76d613c9ce79edc5cb68fd",
                "sha256:aa0cb481c4041bf52ffa7b0d8fa6cd3e88a2ca4879c533c9153882ee2556790d"
            ],
            "version": "==0.8.1"
        },
        "pexpect": {
            "hashes": [
                "sha256:0b48a55dcb3c05f3329815901ea4fc1537514d6ba867a152b581d69ae3710937",
                "sha256:fc65a43959d153d0114afe13997d439c22823a27cefceb5ff35c2178c6784c0c"
            ],
            "markers": "sys_platform != 'win32'",
            "version": "==4.8.0"
        },
        "pickleshare": {
            "hashes": [
                "sha256:87683d47965c1da65cdacaf31c8441d12b8044cdec9aca500cd78fc2c683afca",
                "sha256:9649af414d74d4df115d5d718f82acb59c9d418196b7b4290ed47a12ce62df56"
            ],
            "version": "==0.7.5"
        },
        "pipfile-requirements": {
            "hashes": [
                "sha256:d47591d46d8bfecf9257967992feae31fa83aff7ab6417373c7de5ea92ab849f",
                "sha256:dc2ff7515ce35f8b37a500e87e7b9cd39f0f5c18eb6024543366eb6d4226869b"
            ],
            "index": "pypi",
            "version": "==0.3.0"
        },
        "pluggy": {
            "hashes": [
                "sha256:15b2acde666561e1298d71b523007ed7364de07029219b604cf808bfa1c765b0",
                "sha256:966c145cd83c96502c3c3868f50408687b38434af77734af1e9ca461a4081d2d"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==0.13.1"
        },
        "prompt-toolkit": {
            "hashes": [
                "sha256:d2b91517488f1478ee30f938303a3d60b04cc0b7c2253e7c83f1b9b7635274b4",
                "sha256:e2d04e0e4de0c0a8b67db89a5be6dcf81fed6ca7e8c4affca8b7a5b8595c19dd"
            ],
            "index": "pypi",
            "version": "==3.0.13"
        },
        "ptyprocess": {
            "hashes": [
                "sha256:4b41f3967fce3af57cc7e94b888626c18bf37a083e3651ca8feeb66d492fef35",
                "sha256:5c5d0a3b48ceee0b48485e0c26037c0acd7d29765ca3fbb5cb3831d347423220"
            ],
            "version": "==0.7.0"
        },
        "py": {
            "hashes": [
                "sha256:21b81bda15b66ef5e1a777a21c4dcd9c20ad3efd0b3f817e7a809035269e1bd3",
                "sha256:3b80836aa6d1feeaa108e046da6423ab8f6ceda6468545ae8d02d9d58d18818a"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.10.0"
        },
        "pyaud": {
            "editable": true,
            "path": "."
        },
        "pyblake2": {
            "hashes": [
                "sha256:3757f7ad709b0e1b2a6b3919fa79fe3261f166fc375cd521f2be480f8319dde9",
                "sha256:407e02c7f8f36fcec1b7aa114ddca0c1060c598142ea6f6759d03710b946a7e3",
                "sha256:4d47b4a2c1d292b1e460bde1dda4d13aa792ed2ed70fcc263b6bc24632c8e902",
                "sha256:5ccc7eb02edb82fafb8adbb90746af71460fbc29aa0f822526fc976dff83e93f",
                "sha256:8043267fbc0b2f3748c6920591cd0b8b5609dcce60c504c32858aa36206386f2",
                "sha256:982295a87907d50f4723db6bc724660da76b6547826d52160171d54f95b919ac",
                "sha256:baa2190bfe549e36163aa44664d4ee3a9080b236fc5d42f50dc6fd36bbdc749e",
                "sha256:c53417ee0bbe77db852d5fd1036749f03696ebc2265de359fe17418d800196c4",
                "sha256:fbc9fcde75713930bc2a91b149e97be2401f7c9c56d735b46a109210f58d7358"
            ],
            "index": "pypi",
            "version": "==1.1.2"
        },
        "pygments": {
            "hashes": [
                "sha256:bc9591213a8f0e0ca1a5e68a479b4887fdc3e75d0774e5c71c31920c427de435",
                "sha256:df49d09b498e83c1a73128295860250b0b7edd4c723a32e9bc0d295c7c2ec337"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==2.7.4"
        },
        "pylint": {
            "hashes": [
                "sha256:bb4a908c9dadbc3aac18860550e870f58e1a02c9f2c204fdf5693d73be061210",
                "sha256:bfe68f020f8a0fece830a22dd4d5dddb4ecc6137db04face4c3420a46a52239f"
            ],
            "index": "pypi",
            "version": "==2.6.0"
        },
        "pyparsing": {
            "hashes": [
                "sha256:c203ec8783bf771a155b207279b9bccb8dea02d8f0c9e5f8ead507bc3246ecc1",
                "sha256:ef9d7589ef3c200abe66653d3f1ab1033c3c419ae9b9bdb1240a85b024efc88b"
            ],
            "markers": "python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==2.4.7"
        },
        "pytest": {
            "hashes": [
                "sha256:1969f797a1a0dbd8ccf0fecc80262312729afea9c17f1d70ebf85c5e76c6f7c8",
                "sha256:66e419b1899bc27346cb2c993e12c5e5e8daba9073c1fbce33b9807abc95c306"
            ],
            "index": "pypi",
            "version": "==6.2.1"
        },
        "pytest-cov": {
            "hashes": [
                "sha256:359952d9d39b9f822d9d29324483e7ba04a3a17dd7d05aa6beb7ea01e359e5f7",
                "sha256:bdb9fdb0b85a7cc825269a4c56b48ccaa5c7e365054b6038772c32ddcdc969da"
            ],
            "index": "pypi",
            "version": "==2.11.1"
        },
        "pytest-logging": {
            "hashes": [
                "sha256:cec5c85ecf18aab7b2ead5498a31b9f758680ef5a902b9054ab3f2bdbb77c896"
            ],
            "version": "==2015.11.4"
        },
        "pytz": {
            "hashes": [
                "sha256:16962c5fb8db4a8f63a26646d8886e9d769b6c511543557bc84e9569fb9a9cb4",
                "sha256:180befebb1927b16f6b57101720075a984c019ac16b1b7575673bea42c6c3da5"
            ],
            "version": "==2020.5"
        },
        "readme-renderer": {
            "hashes": [
                "sha256:267854ac3b1530633c2394ead828afcd060fc273217c42ac36b6be9c42cd9a9d",
                "sha256:6b7e5aa59210a40de72eb79931491eaf46fefca2952b9181268bd7c7c65c260a"
            ],
            "version": "==28.0"
        },
        "regex": {
            "hashes": [
                "sha256:02951b7dacb123d8ea6da44fe45ddd084aa6777d4b2454fa0da61d569c6fa538",
                "sha256:0d08e71e70c0237883d0bef12cad5145b84c3705e9c6a588b2a9c7080e5af2a4",
                "sha256:1862a9d9194fae76a7aaf0150d5f2a8ec1da89e8b55890b1786b8f88a0f619dc",
                "sha256:1ab79fcb02b930de09c76d024d279686ec5d532eb814fd0ed1e0051eb8bd2daa",
                "sha256:1fa7ee9c2a0e30405e21031d07d7ba8617bc590d391adfc2b7f1e8b99f46f444",
                "sha256:262c6825b309e6485ec2493ffc7e62a13cf13fb2a8b6d212f72bd53ad34118f1",
                "sha256:2a11a3e90bd9901d70a5b31d7dd85114755a581a5da3fc996abfefa48aee78af",
                "sha256:2c99e97d388cd0a8d30f7c514d67887d8021541b875baf09791a3baad48bb4f8",
                "sha256:3128e30d83f2e70b0bed9b2a34e92707d0877e460b402faca908c6667092ada9",
                "sha256:38c8fd190db64f513fe4e1baa59fed086ae71fa45083b6936b52d34df8f86a88",
                "sha256:3bddc701bdd1efa0d5264d2649588cbfda549b2899dc8d50417e47a82e1387ba",
                "sha256:4902e6aa086cbb224241adbc2f06235927d5cdacffb2425c73e6570e8d862364",
                "sha256:49cae022fa13f09be91b2c880e58e14b6da5d10639ed45ca69b85faf039f7a4e",
                "sha256:56e01daca75eae420bce184edd8bb341c8eebb19dd3bce7266332258f9fb9dd7",
                "sha256:5862975b45d451b6db51c2e654990c1820523a5b07100fc6903e9c86575202a0",
                "sha256:6a8ce43923c518c24a2579fda49f093f1397dad5d18346211e46f134fc624e31",
                "sha256:6c54ce4b5d61a7129bad5c5dc279e222afd00e721bf92f9ef09e4fae28755683",
                "sha256:6e4b08c6f8daca7d8f07c8d24e4331ae7953333dbd09c648ed6ebd24db5a10ee",
                "sha256:717881211f46de3ab130b58ec0908267961fadc06e44f974466d1887f865bd5b",
                "sha256:749078d1eb89484db5f34b4012092ad14b327944ee7f1c4f74d6279a6e4d1884",
                "sha256:7913bd25f4ab274ba37bc97ad0e21c31004224ccb02765ad984eef43e04acc6c",
                "sha256:7a25fcbeae08f96a754b45bdc050e1fb94b95cab046bf56b016c25e9ab127b3e",
                "sha256:83d6b356e116ca119db8e7c6fc2983289d87b27b3fac238cfe5dca529d884562",
                "sha256:8b882a78c320478b12ff024e81dc7d43c1462aa4a3341c754ee65d857a521f85",
                "sha256:8f6a2229e8ad946e36815f2a03386bb8353d4bde368fdf8ca5f0cb97264d3b5c",
                "sha256:9801c4c1d9ae6a70aeb2128e5b4b68c45d4f0af0d1535500884d644fa9b768c6",
                "sha256:a15f64ae3a027b64496a71ab1f722355e570c3fac5ba2801cafce846bf5af01d",
                "sha256:a3d748383762e56337c39ab35c6ed4deb88df5326f97a38946ddd19028ecce6b",
                "sha256:a63f1a07932c9686d2d416fb295ec2c01ab246e89b4d58e5fa468089cab44b70",
                "sha256:b2b1a5ddae3677d89b686e5c625fc5547c6e492bd755b520de5332773a8af06b",
                "sha256:b2f4007bff007c96a173e24dcda236e5e83bde4358a557f9ccf5e014439eae4b",
                "sha256:baf378ba6151f6e272824b86a774326f692bc2ef4cc5ce8d5bc76e38c813a55f",
                "sha256:bafb01b4688833e099d79e7efd23f99172f501a15c44f21ea2118681473fdba0",
                "sha256:bba349276b126947b014e50ab3316c027cac1495992f10e5682dc677b3dfa0c5",
                "sha256:c084582d4215593f2f1d28b65d2a2f3aceff8342aa85afd7be23a9cad74a0de5",
                "sha256:d1ebb090a426db66dd80df8ca85adc4abfcbad8a7c2e9a5ec7513ede522e0a8f",
                "sha256:d2d8ce12b7c12c87e41123997ebaf1a5767a5be3ec545f64675388970f415e2e",
                "sha256:e32f5f3d1b1c663af7f9c4c1e72e6ffe9a78c03a31e149259f531e0fed826512",
                "sha256:e3faaf10a0d1e8e23a9b51d1900b72e1635c2d5b0e1bea1c18022486a8e2e52d",
                "sha256:f7d29a6fc4760300f86ae329e3b6ca28ea9c20823df123a2ea8693e967b29917",
                "sha256:f8f295db00ef5f8bae530fc39af0b40486ca6068733fb860b42115052206466f"
            ],
            "version": "==2020.11.13"
        },
        "requests": {
            "hashes": [
                "sha256:27973dd4a904a4f13b263a19c866c13b92a39ed1c964655f025f3f8d3d75b804",
                "sha256:c210084e36a42ae6b9219e00e48287def368a26d03a048ddad7bfee44f75871e"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4'",
            "version": "==2.25.1"
        },
        "restview": {
            "hashes": [
                "sha256:47929bae12e7cf39cbb93a5a5a16f970941e39301c05cbb4ea398df8c113b1e2",
                "sha256:790097eb587c0465126dde73ca06c7a22c5007ce1be4a1de449a13c0767b32dc"
            ],
            "index": "pypi",
            "version": "==2.9.2"
        },
        "six": {
            "hashes": [
                "sha256:30639c035cdb23534cd4aa2dd52c3bf48f06e5f4a941509c8bafd8ce11080259",
                "sha256:8b74bedcbbbaca38ff6d7491d76f2b06b3592611af620f8426e82dddb04a5ced"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==1.15.0"
        },
        "snowballstemmer": {
            "hashes": [
                "sha256:b51b447bea85f9968c13b650126a888aabd4cb4463fca868ec596826325dedc2",
                "sha256:e997baa4f2e9139951b6f4c631bad912dfd3c792467e2f03d7239464af90e914"
            ],
            "version": "==2.1.0"
        },
        "sphinx": {
            "hashes": [
                "sha256:41cad293f954f7d37f803d97eb184158cfd90f51195131e94875bc07cd08b93c",
                "sha256:c314c857e7cd47c856d2c5adff514ac2e6495f8b8e0f886a8a37e9305dfea0d8"
            ],
            "index": "pypi",
            "version": "==3.4.3"
        },
        "sphinxcontrib-applehelp": {
            "hashes": [
                "sha256:806111e5e962be97c29ec4c1e7fe277bfd19e9652fb1a4392105b43e01af885a",
                "sha256:a072735ec80e7675e3f432fcae8610ecf509c5f1869d17e2eecff44389cdbc58"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.2"
        },
        "sphinxcontrib-devhelp": {
            "hashes": [
                "sha256:8165223f9a335cc1af7ffe1ed31d2871f325254c0423bc0c4c7cd1c1e4734a2e",
                "sha256:ff7f1afa7b9642e7060379360a67e9c41e8f3121f2ce9164266f61b9f4b338e4"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.2"
        },
        "sphinxcontrib-fulltoc": {
            "hashes": [
                "sha256:c845d62fc467f3135d4543e9f10e13ef91852683bd1c90fd19d07f9d36757cd9"
            ],
            "index": "pypi",
            "version": "==1.2.0"
        },
        "sphinxcontrib-htmlhelp": {
            "hashes": [
                "sha256:3c0bc24a2c41e340ac37c85ced6dafc879ab485c095b1d65d2461ac2f7cca86f",
                "sha256:e8f5bb7e31b2dbb25b9cc435c8ab7a79787ebf7f906155729338f3156d93659b"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.3"
        },
        "sphinxcontrib-jsmath": {
            "hashes": [
                "sha256:2ec2eaebfb78f3f2078e73666b1415417a116cc848b72e5172e596c871103178",
                "sha256:a9925e4a4587247ed2191a22df5f6970656cb8ca2bd6284309578f2153e0c4b8"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.1"
        },
        "sphinxcontrib-programoutput": {
            "hashes": [
                "sha256:0caaa216d0ad8d2cfa90a9a9dba76820e376da6e3152be28d10aedc09f82a3b0",
                "sha256:8009d1326b89cd029ee477ce32b45c58d92b8504d48811461c3117014a8f4b1e"
            ],
            "index": "pypi",
            "version": "==0.16"
        },
        "sphinxcontrib-qthelp": {
            "hashes": [
                "sha256:4c33767ee058b70dba89a6fc5c1892c0d57a54be67ddd3e7875a18d14cba5a72",
                "sha256:bd9fc24bcb748a8d51fd4ecaade681350aa63009a347a8c14e637895444dfab6"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.0.3"
        },
        "sphinxcontrib-serializinghtml": {
            "hashes": [
                "sha256:eaa0eccc86e982a9b939b2b82d12cc5d013385ba5eadcc7e4fed23f4405f77bc",
                "sha256:f242a81d423f59617a8e5cf16f5d4d74e28ee9a66f9e5b637a18082991db5a9a"
            ],
            "markers": "python_version >= '3.5'",
            "version": "==1.1.4"
        },
        "toml": {
            "hashes": [
                "sha256:806143ae5bfb6a3c6e736a764057db0e6a0e05e338b5630894a5f779cabb4f9b",
                "sha256:b3bda1d108d5dd99f4a20d24d9c348e91c4db7ab1b749200bded2f839ccbe68f"
            ],
            "markers": "python_version >= '2.6' and python_version not in '3.0, 3.1, 3.2, 3.3'",
            "version": "==0.10.2"
        },
        "traitlets": {
            "hashes": [
                "sha256:178f4ce988f69189f7e523337a3e11d91c786ded9360174a3d9ca83e79bc5396",
                "sha256:69ff3f9d5351f31a7ad80443c2674b7099df13cc41fc5fa6e2f6d3b0330b0426"
            ],
            "markers": "python_version >= '3.7'",
            "version": "==5.0.5"
        },
        "typed-ast": {
            "hashes": [
                "sha256:07d49388d5bf7e863f7fa2f124b1b1d89d8aa0e2f7812faff0a5658c01c59aa1",
                "sha256:14bf1522cdee369e8f5581238edac09150c765ec1cb33615855889cf33dcb92d",
                "sha256:240296b27397e4e37874abb1df2a608a92df85cf3e2a04d0d4d61055c8305ba6",
                "sha256:36d829b31ab67d6fcb30e185ec996e1f72b892255a745d3a82138c97d21ed1cd",
                "sha256:37f48d46d733d57cc70fd5f30572d11ab8ed92da6e6b28e024e4a3edfb456e37",
                "sha256:4c790331247081ea7c632a76d5b2a265e6d325ecd3179d06e9cf8d46d90dd151",
                "sha256:5dcfc2e264bd8a1db8b11a892bd1647154ce03eeba94b461effe68790d8b8e07",
                "sha256:7147e2a76c75f0f64c4319886e7639e490fee87c9d25cb1d4faef1d8cf83a440",
                "sha256:7703620125e4fb79b64aa52427ec192822e9f45d37d4b6625ab37ef403e1df70",
                "sha256:8368f83e93c7156ccd40e49a783a6a6850ca25b556c0fa0240ed0f659d2fe496",
                "sha256:84aa6223d71012c68d577c83f4e7db50d11d6b1399a9c779046d75e24bed74ea",
                "sha256:85f95aa97a35bdb2f2f7d10ec5bbdac0aeb9dafdaf88e17492da0504de2e6400",
                "sha256:8db0e856712f79c45956da0c9a40ca4246abc3485ae0d7ecc86a20f5e4c09abc",
                "sha256:9044ef2df88d7f33692ae3f18d3be63dec69c4fb1b5a4a9ac950f9b4ba571606",
                "sha256:963c80b583b0661918718b095e02303d8078950b26cc00b5e5ea9ababe0de1fc",
                "sha256:987f15737aba2ab5f3928c617ccf1ce412e2e321c77ab16ca5a293e7bbffd581",
                "sha256:9ec45db0c766f196ae629e509f059ff05fc3148f9ffd28f3cfe75d4afb485412",
                "sha256:9fc0b3cb5d1720e7141d103cf4819aea239f7d136acf9ee4a69b047b7986175a",
                "sha256:a2c927c49f2029291fbabd673d51a2180038f8cd5a5b2f290f78c4516be48be2",
                "sha256:a38878a223bdd37c9709d07cd357bb79f4c760b29210e14ad0fb395294583787",
                "sha256:b4fcdcfa302538f70929eb7b392f536a237cbe2ed9cba88e3bf5027b39f5f77f",
                "sha256:c0c74e5579af4b977c8b932f40a5464764b2f86681327410aa028a22d2f54937",
                "sha256:c1c876fd795b36126f773db9cbb393f19808edd2637e00fd6caba0e25f2c7b64",
                "sha256:c9aadc4924d4b5799112837b226160428524a9a45f830e0d0f184b19e4090487",
                "sha256:cc7b98bf58167b7f2db91a4327da24fb93368838eb84a44c472283778fc2446b",
                "sha256:cf54cfa843f297991b7388c281cb3855d911137223c6b6d2dd82a47ae5125a41",
                "sha256:d003156bb6a59cda9050e983441b7fa2487f7800d76bdc065566b7d728b4581a",
                "sha256:d175297e9533d8d37437abc14e8a83cbc68af93cc9c1c59c2c292ec59a0697a3",
                "sha256:d746a437cdbca200622385305aedd9aef68e8a645e385cc483bdc5e488f07166",
                "sha256:e683e409e5c45d5c9082dc1daf13f6374300806240719f95dc783d1fc942af10"
            ],
            "version": "==1.4.2"
        },
        "typing-extensions": {
            "hashes": [
                "sha256:7cb407020f00f7bfc3cb3e7881628838e69d8f3fcab2f64742a5e76b2f841918",
                "sha256:99d4073b617d30288f569d3f13d2bd7548c3a7e4c8de87db09a9d29bb3a4a60c",
                "sha256:dafc7639cde7f1b6e1acc0f457842a83e722ccca8eef5270af2d74792619a89f"
            ],
            "version": "==3.7.4.3"
        },
        "urllib3": {
            "hashes": [
                "sha256:19188f96923873c92ccb987120ec4acaa12f0461fa9ce5d3d0772bc965a39e08",
                "sha256:d8ff90d979214d7b4f8ce956e80f4028fc6860e4431f731ea4a8c08f23f99473"
            ],
            "markers": "python_version >= '2.7' and python_version not in '3.0, 3.1, 3.2, 3.3, 3.4' and python_version < '4.0'",
            "version": "==1.26.2"
        },
        "vulture": {
            "hashes": [
                "sha256:03d5a62bcbe9ceb9a9b0575f42d71a2d414070229f2e6f95fa6e7c71aaaed967",
                "sha256:f39de5e6f1df1f70c3b50da54f1c8d494159e9ca3d01a9b89eac929600591703"
            ],
            "index": "pypi",
            "version": "==2.3"
        },
        "wcwidth": {
            "hashes": [
                "sha256:beb4802a9cebb9144e99086eff703a642a13d6a0052920003a230f3294bbe784",
                "sha256:c4d647b99872929fdb7bdcaa4fbe7f01413ed3d98077df798530e5b04f116c83"
            ],
            "version": "==0.2.5"
        },
        "webencodings": {
            "hashes": [
                "sha256:a0af1213f3c2226497a97e2b3aa01a7e4bee4f403f95be16fc9acd2947514a78",
                "sha256:b36a1c245f2d304965eb4e0a82848379241dc04b865afcc4aab16748587e1923"
            ],
            "version": "==0.5.1"
        },
        "wrapt": {
            "hashes": [
                "sha256:b62ffa81fb85f4332a4f609cab4ac40709470da05643a082ec1eb88e6d9b97d7"
            ],
            "version": "==1.12.1"
        }
    }
}
"""
DEFAULT_TOC = """
repo package
============

Module contents
---------------

.. automodule:: repo
   :members:
   :undoc-members:
   :show-inheritance:
"""
REQUIREMENTS = """
-e .
alabaster==0.7.12
appdirs==1.4.4
astroid==2.4.2
attrs==20.3.0
babel==2.9.0
backcall==0.2.0
black==20.8b1
bleach==3.2.2
certifi==2020.12.5
chardet==4.0.0
click==7.1.2
codecov==2.1.11
coverage[toml]==5.3.1
decorator==4.4.2
docutils==0.16
gprof2dot==2019.11.30
idna==2.10
imagesize==1.2.0
iniconfig==1.1.1
ipython-genutils==0.2.0
ipython==7.19.0
isort==5.7.0
jedi==0.18.0
jinja2==2.11.2
lazy-object-proxy==1.4.3
markupsafe==1.1.1
mccabe==0.6.1
mypy-extensions==0.4.3
mypy==0.800
object-colors==1.0.8
packaging==20.8
parso==0.8.1
pathspec==0.8.1
pexpect==4.8.0
pickleshare==0.7.5
pipfile-requirements==0.3.0
pluggy==0.13.1
prompt-toolkit==3.0.13
ptyprocess==0.7.0
py==1.10.0
pyblake2==1.1.2
pygments==2.7.4
pylint==2.6.0
pyparsing==2.4.7
pytest-cov==2.11.1
pytest-logging==2015.11.4
pytest-profiling==1.7.0
pytest-randomly==3.5.0
pytest-sugar==0.9.4
pytest==6.2.1
pytz==2020.5
readme-renderer==28.0
regex==2020.11.13
requests==2.25.1
restview==2.9.2
six==1.15.0
snowballstemmer==2.1.0
sphinx==3.4.3
sphinxcontrib-applehelp==1.0.2
sphinxcontrib-devhelp==1.0.2
sphinxcontrib-fulltoc==1.2.0
sphinxcontrib-htmlhelp==1.0.3
sphinxcontrib-jsmath==1.0.1
sphinxcontrib-programoutput==0.16
sphinxcontrib-qthelp==1.0.3
sphinxcontrib-serializinghtml==1.1.4
termcolor==1.1.0
toml==0.10.2
traitlets==5.0.5
typed-ast==1.4.2
typing-extensions==3.7.4.3
urllib3==1.26.2
vulture==2.3
wcwidth==0.2.5
webencodings==0.5.1
wrapt==1.12.1
"""
PIPFILE2REQ_PROD = """
alabaster==0.7.12
appdirs==1.4.4
astroid==2.4.2; python_version >= "3.5"
attrs==20.3.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
babel==2.9.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
black==20.8b1
certifi==2020.12.5
chardet==4.0.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
click==7.1.2; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
codecov==2.1.11
coverage[toml]==5.3.1
docutils==0.16; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
gprof2dot==2019.11.30
idna==2.10; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
imagesize==1.2.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
iniconfig==1.1.1
isort==5.7.0; python_version >= "3.6" and python_version < "4.0"
jinja2==2.11.2; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
lazy-object-proxy==1.4.3; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
markupsafe==1.1.1; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
mccabe==0.6.1
mypy==0.800
mypy-extensions==0.4.3
object-colors==1.0.8
packaging==20.8; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
pathspec==0.8.1
pipfile-requirements==0.3.0
pluggy==0.13.1; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
py==1.10.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
pyblake2==1.1.2
pygments==2.7.4; python_version >= "3.5"
pylint==2.6.0
pyparsing==2.4.7; python_version >= "2.6" and python_version not in "3.0, 3.1, 3.2, 3.3"
pytest==6.2.1
pytest-cov==2.11.1
pytest-profiling==1.7.0
pytest-randomly==3.5.0
pytest-sugar==0.9.4
pytz==2020.5
regex==2020.11.13
requests==2.25.1; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
six==1.15.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
snowballstemmer==2.1.0
sphinx==3.4.3
sphinxcontrib-applehelp==1.0.2; python_version >= "3.5"
sphinxcontrib-devhelp==1.0.2; python_version >= "3.5"
sphinxcontrib-fulltoc==1.2.0
sphinxcontrib-htmlhelp==1.0.3; python_version >= "3.5"
sphinxcontrib-jsmath==1.0.1; python_version >= "3.5"
sphinxcontrib-programoutput==0.16
sphinxcontrib-qthelp==1.0.3; python_version >= "3.5"
sphinxcontrib-serializinghtml==1.1.4; python_version >= "3.5"
termcolor==1.1.0
toml==0.10.2; python_version >= "2.6" and python_version not in "3.0, 3.1, 3.2, 3.3"
typed-ast==1.4.2
typing-extensions==3.7.4.3
urllib3==1.26.2; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4" and python_version < "4.0"
vulture==2.3
wrapt==1.12.1
"""
PIPFILE2REQ_DEV = """
alabaster==0.7.12
appdirs==1.4.4
astroid==2.4.2; python_version >= "3.5"
attrs==20.3.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
babel==2.9.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
backcall==0.2.0
black==20.8b1
bleach==3.2.2; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
certifi==2020.12.5
chardet==4.0.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
click==7.1.2; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
codecov==2.1.11
coverage[toml]==5.3.1
decorator==4.4.2
docutils==0.16; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
idna==2.10; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
imagesize==1.2.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
iniconfig==1.1.1
ipython==7.19.0
ipython-genutils==0.2.0
isort==5.7.0; python_version >= "3.6" and python_version < "4.0"
jedi==0.18.0; python_version >= "3.6"
jinja2==2.11.2; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
lazy-object-proxy==1.4.3; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
markupsafe==1.1.1; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
mccabe==0.6.1
mypy==0.800
mypy-extensions==0.4.3
object-colors==1.0.8
packaging==20.8; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
parso==0.8.1; python_version >= "3.6"
pathspec==0.8.1
pexpect==4.8.0; sys_platform != "win32"
pickleshare==0.7.5
pipfile-requirements==0.3.0
pluggy==0.13.1; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
prompt-toolkit==3.0.13
ptyprocess==0.7.0
py==1.10.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
-e .
pyblake2==1.1.2
pygments==2.7.4; python_version >= "3.5"
pylint==2.6.0
pyparsing==2.4.7; python_version >= "2.6" and python_version not in "3.0, 3.1, 3.2, 3.3"
pytest==6.2.1
pytest-cov==2.11.1
pytest-logging==2015.11.4
pytz==2020.5
readme-renderer==28.0
regex==2020.11.13
requests==2.25.1; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4"
restview==2.9.2
six==1.15.0; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3"
snowballstemmer==2.1.0
sphinx==3.4.3
sphinxcontrib-applehelp==1.0.2; python_version >= "3.5"
sphinxcontrib-devhelp==1.0.2; python_version >= "3.5"
sphinxcontrib-fulltoc==1.2.0
sphinxcontrib-htmlhelp==1.0.3; python_version >= "3.5"
sphinxcontrib-jsmath==1.0.1; python_version >= "3.5"
sphinxcontrib-programoutput==0.16
sphinxcontrib-qthelp==1.0.3; python_version >= "3.5"
sphinxcontrib-serializinghtml==1.1.4; python_version >= "3.5"
toml==0.10.2; python_version >= "2.6" and python_version not in "3.0, 3.1, 3.2, 3.3"
traitlets==5.0.5; python_version >= "3.7"
typed-ast==1.4.2
typing-extensions==3.7.4.3
urllib3==1.26.2; python_version >= "2.7" and python_version not in "3.0, 3.1, 3.2, 3.3, 3.4" and python_version < "4.0"
vulture==2.3
wcwidth==0.2.5
webencodings==0.5.1
wrapt==1.12.1
"""
IMPORTS_UNSORTED = """
from typing import Union, Callable, List, Any
from pyaud import (
    colors,
    Subprocess,
    write_command,
    HashCap,
    config,
    Git,
    LineSwitch,
    check_command,
    print_command,
    environ,
    PyaudSubprocessError,
    EnterDir,
    pyitems
)
import shutil
import pathlib
import os

_ = (
    Git,
    List,
    pathlib,
    os,
    colors,
    config,
    check_command,
    Callable,
    PyaudSubprocessError,
    write_command,
    shutil,
    EnterDir,
    LineSwitch,
    Union,
    HashCap,
    pyitems,
    Any,
    Subprocess,
    print_command,
    environ,
)
"""
IMPORTS_SORTED = """
import os
import pathlib
import shutil
from typing import Any, Callable, List, Union

from pyaud import (
    EnterDir,
    Git,
    HashCap,
    LineSwitch,
    PyaudSubprocessError,
    Subprocess,
    check_command,
    colors,
    config,
    environ,
    print_command,
    pyitems,
    write_command,
)
"""
CODE_BLOCK_TEMPLATE = """
.. code-block:: python

    >>> print("Hello, world!")
    'Hello, world!'
..
"""
SUCCESS = "\n{}\nSuccess!".format(80 * "-")
CODE_BLOCK_EXPECTED = (
    '\ncode-block 1\n. >>> print("Hello, world!")\nHello, world!\n{}'.format(
        SUCCESS
    )
)


class Whitelist:  # pylint: disable=too-few-public-methods
    """Output for whitelist.py on commit be8a443"""

    be8a443_tests = """fixture_is_env_path_var  # unused function (tests/conftest.py:16)
fixture_call_status  # unused function (tests/conftest.py:228)
fixture_commit_test  # unused function (tests/conftest.py:160)
fixture_main  # unused function (tests/conftest.py:211)
fixture_make_default_toc  # unused function (tests/conftest.py:345)
fixture_make_deploy_docs_env  # unused function (tests/conftest.py:378)
fixture_make_project_tree  # unused function (tests/conftest.py:336)
fixture_make_python_file  # unused function (tests/conftest.py:359)
fixture_make_test_file  # unused function (tests/conftest.py:365)
fixture_make_tree  # unused function (tests/conftest.py:307)
fixture_make_written  # unused function (tests/conftest.py:298)
fixture_mock_environment  # unused function (tests/conftest.py:86)
fixture_mock_make_docs  # unused function (tests/conftest.py:402)
fixture_mock_remote_origin  # unused function (tests/conftest.py:184)
fixture_nocolorcapsys  # unused function (tests/conftest.py:199)
fixture_patch_sp_call  # unused function (tests/conftest.py:241)
fixture_patch_sp_returncode  # unused function (tests/conftest.py:264)
fixture_project_dir  # unused function (tests/conftest.py:73)
fixture_set_git_creds  # unused function (tests/conftest.py:152)
fixture_test_logging  # unused function (tests/conftest.py:61)
fixture_track_called  # unused function (tests/conftest.py:281)
fixture_validate_env  # unused function (tests/conftest.py:33)
"""
    be8a443_pyaud = """_.clone  # unused method (pyaud/src/__init__.py:223)
_.propagate  # unused attribute (pyaud/src/__init__.py:463)
exc_tb  # unused variable (pyaud/src/__init__.py:256)
exc_tb  # unused variable (pyaud/src/__init__.py:299)
exc_tb  # unused variable (pyaud/src/__init__.py:381)
exc_type  # unused variable (pyaud/src/__init__.py:256)
exc_type  # unused variable (pyaud/src/__init__.py:299)
exc_type  # unused variable (pyaud/src/__init__.py:381)
exc_val  # unused variable (pyaud/src/__init__.py:256)
exc_val  # unused variable (pyaud/src/__init__.py:299)
exc_val  # unused variable (pyaud/src/__init__.py:381)
make_audit  # unused function (pyaud/src/modules.py:26)
make_files  # unused function (pyaud/src/modules.py:205)
"""

    @classmethod
    def be8a443_all(cls):
        """Concatenate and sort the two files worth of whitelist text.

        :return: Concatenated and sorted ``str``.
        """
        seq = f"{cls.be8a443_pyaud}{cls.be8a443_tests}".splitlines()
        seq.sort()
        return "{}\n".format("\n".join(seq))
