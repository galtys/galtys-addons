# pool -> env
find . -type f -name '*.py' | xargs sed -i 's/self.pool/self.env/g'
# remove cr, uid
find . -type f -name '*.py' | xargs sed -i 's/(cr, [^,]*, /(/g'
find . -type f -name '*.py' | xargs sed -i 's/(self, cr, [^,]*, ids/(self/g'
find . -type f -name '*.py' | xargs sed -i 's/(self, cr, uid, /(self, /g'
find . -type f -name '*.py' | xargs sed -i 's/, context=[^,)]*//g'
find . -type f -name '*.py' | xargs sed -i 's/self.env.get(\([^)]*\))/self.env[\1]/g'
# res_config.py
find . -type f -name 'res_config.py' | xargs sed -i 's/\(def get_default_.*\)(self)/\1(self, fields)/g'
