from odoo import api, fields, models, tools, SUPERUSER_ID, _

class Person(models.Model):
    _name = "hashsync.demo.person"
    _description = "Person"
    
    code= fields.Char("code")
    secret_key = fields.Char("secret_key")
    name = fields.Char("Name")
    birth_date = fields.Date("Birth Date")
    address_ids = fields.One2many('hashsync.demo.address','person_id','Addresses')

class Address(models.Model):
    _name = "hashsync.demo.address"
    _description = "Address"
    _name_rec = "street"
    
    code= fields.Char("code")
    secret_key = fields.Char("secret_key")
    street = fields.Char("street")
    street2 = fields.Char("street2")
    city= fields.Char("city")
    zip = fields.Char("zip")
    person_id = fields.Many2one("hashsync.demo.person", "Person")
