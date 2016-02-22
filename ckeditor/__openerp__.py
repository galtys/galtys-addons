
{
    'name': 'ckeditor',
    'description': """
    widget for editing html fields via CKEditor 4.x
    you need specific features of ckeditor, use widget="ckeditor".
    """,
    "category": "Tools",
    "depends": [
        'web',
        ],
    'css': [
        'static/src/css/ckeditor.css',
        ],
    'data': [
        ],
    'js': [
        'static/src/js/ckeditor_basepath.js',
        'static/lib/ckeditor/ckeditor.js',
        'static/lib/ckeditor/config.js',
        'static/src/js/ckeditor.js',
        ],
    'installable': True,
    'auto_install': False,
    'certificate': '',
}
