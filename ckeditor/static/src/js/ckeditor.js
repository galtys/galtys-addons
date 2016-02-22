openerp.ckeditor = function(openerp)
{
    var ckeditor_addFunction_org = CKEDITOR.tools.addFunction;
    CKEDITOR.tools.addFunction = function(fn, scope)
    {
        if(scope && scope._ && scope._.attrChanges && scope._.detach)
        {
            var scope_reference = scope;
            return ckeditor_addFunction_org(function()
                    {
                        var self = this,
                            self_arguments=arguments;
                        setTimeout(function()
                        {
                            if(CKEDITOR.instances[self.editor.name])
                            {
                                fn.apply(self, self_arguments);
                            }
                        }, 0);
                    }, scope);
        }
        return ckeditor_addFunction_org(fn, scope);
    };

    CKEDITOR.on('dialogDefinition', function(e)
        {
            _.each(e.data.definition.contents, function(element)
            {
                if(!element || element.filebrowser!='uploadButton')
                {
                    return
                }
                _.each(element.elements, function(element)
                {
                    if(!element.onClick || element.type!='fileButton')
                    {
                        return
                    }
                    var onClick_org = element.onClick;
                    element.onClick = function(e1)
                    {
                        onClick_org.apply(this, arguments);
                        _.each(jQuery('#'+this.domId).closest('table')
                            .find('iframe').contents().find(':file')
                            .get(0).files,
                            function(file)
                            {
                                var reader = new FileReader();
                                reader.onload = function(load_event)
                                {
                                    CKEDITOR.tools.callFunction(
                                        e.editor._.filebrowserFn,
                                        load_event.target.result,
                                        '');
                                }
                                reader.readAsDataURL(file);
                            });
                        return false;
                    }
                });
            });
        });

    openerp.web.form.widgets.add('ckeditor',
            'openerp.ckeditor.FieldCKEditor4');

    function filter_html(value, ckeditor_filter, ckeditor_writer)
    {
        var fragment = CKEDITOR.htmlParser.fragment.fromHtml(value);
        ckeditor_filter.applyTo(fragment);
        ckeditor_writer.reset();
        fragment.writeHtml(ckeditor_writer);
        return ckeditor_writer.getHtml();
    };

    default_ckeditor_filter = new CKEDITOR.filter(
            {
                '*':
                {
                    attributes: 'href,src,style,alt,width,height,dir',
                    styles: '*',
                    classes: '*',
                },
                'html head title meta style body p div span a h1 h2 h3 h4 h5 img br hr table tr th td ul ol li dd dt strong pre b i': true,
            });
    default_ckeditor_writer = new CKEDITOR.htmlParser.basicWriter();

    openerp.ckeditor.FieldCKEditor4 = openerp.web.form.FieldText.extend({
        ckeditor_config: {
            removePlugins: 'iframe,flash,forms,smiley,pagebreak,stylescombo',
            filebrowserImageUploadUrl: 'dummy',
            extraPlugins: 'filebrowser',
        },
        ckeditor_filter: default_ckeditor_filter,
        ckeditor_writer: default_ckeditor_writer,
        start: function()
        {
            this._super.apply(this, arguments);
    
            CKEDITOR.lang.load(openerp.session.user_context.lang.split('_')[0], 'en', function() {});
        },
        initialize_content: function()
        {
            var self = this;
            this._super.apply(this, arguments);
            if(!this.$textarea)
            {
                return;
            }
            this.editor = CKEDITOR.replace(this.$textarea.get(0),
                _.extend(
                    {
                        language: openerp.session.user_context.lang.split('_')[0],
                        on:
                        {
                            'change': function()
                            {
                                self.store_dom_value();
                            },
                        },
                    }, 
                    this.ckeditor_config));
        },
        store_dom_value: function()
        {
            this.internal_set_value(this.editor ? this.editor.getData() : openerp.web.parse_value(this.get('value'), this));
        },
        filter_html: function(value)
        {
            return filter_html(value, this.ckeditor_filter, this.ckeditor_writer);
        },
        render_value: function()
        {
            if(this.get("effective_readonly"))
            {
                this.$el.html(this.filter_html(this.get('value')));
            }
            else
            {
                if(this.editor)
                {
                    var self = this;
                    if(this.editor.status != 'ready')
                    {
                        var instanceReady = function()
                        {
                            self.editor.setData(self.get('value') || '');
                            self.editor.removeListener('instanceReady', instanceReady);
                        };
                        this.editor.on('instanceReady', instanceReady);
                    }
                    else
                    {
                        self.editor.setData(self.get('value') || '');
                    }
                }
            }
        },
        undelegateEvents: function()
        {
            this._cleanup_editor();
            return this._super.apply(this, arguments);
        },
        _cleanup_editor: function()
        {
            if(this.editor)
            {
                CKEDITOR.remove(this.editor);
                this.editor.removeAllListeners();
                this.editor = null;
            }
        },
        destroy_content: function()
        {
            this._cleanup_editor();
        }
    });
}

