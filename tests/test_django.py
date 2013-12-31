from __future__ import absolute_import

import datetime

from .django_app.models import *

from django.core.management import call_command
from django.test import TestCase

from mixer.backend.django import Mixer


class MixerTestDjango(TestCase):

    @classmethod
    def setUpClass(cls):
        call_command('syncdb', interactive=False)

    @classmethod
    def tearDownClass(cls):
        call_command('flush', interactive=False)

    def test_custom(self):
        mixer = Mixer()
        mixer.register(Rabbit, {
            'title': lambda: 'Mr. Rabbit'
        })

        rabbit = mixer.blend(Rabbit)
        self.assertEqual(rabbit.title, 'Mr. Rabbit')

        from mixer.backend.django import GenFactory

        def getter(*args, **kwargs):
            return "Always same"

        class MyFactory(GenFactory):
            generators = {models.CharField: getter}

        gen = MyFactory.gen_maker(models.CharField)
        self.assertEqual(gen(), "Always same")

        mixer = Mixer(factory=MyFactory, fake=False)
        self.assertEqual(mixer._Mixer__factory, MyFactory)

        test = mixer.blend(Rabbit)
        self.assertEqual(test.title, "Always same")

    def test_fields(self):
        mixer = Mixer()
        rabbit = mixer.blend('django_app.rabbit')

        self.assertTrue(isinstance(rabbit, Rabbit))
        self.assertTrue(rabbit.id)
        self.assertTrue(rabbit.pk)
        self.assertEqual(rabbit.pk, 1)
        self.assertEqual(len(rabbit.title), 16)
        self.assertTrue(isinstance(rabbit.active, bool))
        self.assertTrue(isinstance(rabbit.created_at, datetime.date))
        self.assertTrue(isinstance(rabbit.updated_at, datetime.datetime))
        self.assertTrue(isinstance(rabbit.opened_at, datetime.time))
        self.assertTrue('@' in rabbit.email)
        self.assertTrue(rabbit.speed)
        self.assertTrue(rabbit.description)
        self.assertEqual(rabbit.picture.read(), b'pylama\n')

        rabbit = mixer.blend('rabbit')
        self.assertTrue(rabbit)

    def test_random_fields(self):
        mixer = Mixer(fake=False)
        rabbit = mixer.blend('django_app.rabbit')

        self.assertTrue(isinstance(rabbit, Rabbit))
        self.assertTrue(rabbit.id)
        self.assertTrue(rabbit.pk)
        self.assertEqual(rabbit.pk, 1)
        self.assertEqual(len(rabbit.title), 16)
        self.assertTrue(isinstance(rabbit.active, bool))
        self.assertTrue(isinstance(rabbit.created_at, datetime.date))
        self.assertTrue(isinstance(rabbit.updated_at, datetime.datetime))
        self.assertTrue(isinstance(rabbit.opened_at, datetime.time))
        self.assertTrue('@' in rabbit.email)
        self.assertTrue(rabbit.description)
        self.assertTrue(rabbit.some_field)
        self.assertTrue(rabbit.money)

        hat = mixer.blend('django_app.hat', color=mixer.RANDOM)
        self.assertTrue(hat.color in ('RD', 'GRN', 'BL'))

    def test_relation(self):
        mixer = Mixer()

        hole = mixer.blend('django_app.hole', title='hole4')
        self.assertEqual(hole.owner.pk, 1)
        self.assertEqual(hole.title, 'hole4')

        hat = mixer.blend('django_app.hat')
        self.assertFalse(hat.owner)
        self.assertEqual(hat.brend, 'wood')
        self.assertTrue(hat.color in ('RD', 'GRN', 'BL'))

        hat = mixer.blend('django_app.hat', owner=mixer.SELECT)
        self.assertTrue(hat.owner)

        silk = mixer.blend('django_app.silk')
        self.assertFalse(silk.hat.owner)

        silk = mixer.blend('django_app.silk', hat__owner__title='booble')
        self.assertTrue(silk.hat.owner)
        self.assertEqual(silk.hat.owner.title, 'booble')

        door = mixer.blend('django_app.door', hole__title='flash',
                           hole__size=244)
        self.assertTrue(door.hole.owner)
        self.assertEqual(door.hole.title, 'flash')
        self.assertEqual(door.hole.size, 244)

        door = mixer.blend('django_app.door')
        self.assertNotEqual(door.hole.title, 'flash')

        num = mixer.blend('django_app.number', doors=[door])
        self.assertEqual(num.doors.get(), door)

        num = mixer.blend('django_app.number')
        self.assertEqual(num.doors.count(), 1)

        num = mixer.blend('django_app.number', doors__size=42)
        self.assertEqual(num.doors.all()[0].size, 42)

        tag = mixer.blend('django_app.tag', customer=mixer.RANDOM)
        self.assertTrue(tag.customer)

    def test_many_to_many_through(self):
        mixer = Mixer()
        pointa = mixer.blend('django_app.pointa')
        self.assertTrue(pointa.other.all())

        pointb = mixer.blend('pointb')
        pointa = mixer.blend('pointa', other=pointb)
        self.assertEqual(list(pointa.other.all()), [pointb])

    def test_default_mixer(self):
        from mixer.backend.django import mixer

        test = mixer.blend(Rabbit)
        self.assertTrue(test.username)

    def test_select(self):
        from mixer.backend.django import mixer

        mixer.cycle(3).blend(Rabbit)
        hole = mixer.blend(Hole, rabbit=mixer.SELECT)
        self.assertFalse(hole.rabbit)

        rabbits = Rabbit.objects.all()
        hole = mixer.blend(Hole, owner=mixer.SELECT)
        self.assertTrue(hole.owner in rabbits)

        rabbit = rabbits[0]
        hole = mixer.blend(Hole, owner=mixer.SELECT(email=rabbit.email))
        self.assertEqual(hole.owner, rabbit)

    def test_fake(self):
        from mixer.backend.django import mixer

        def postprocess(user):
            user.set_password(user.password)
            return user

        mixer.register('auth.User', {}, postprocess=postprocess)
        user = mixer.blend('auth.User', username=mixer.FAKE, password='test')
        self.assertTrue('' in user.username)
        self.assertTrue(user.check_password('test'))
        user = user.__class__.objects.get(pk=user.pk)
        self.assertTrue(user.check_password('test'))

    def test_random(self):
        from mixer.backend.django import mixer

        user = mixer.blend('auth.User', username=mixer.RANDOM(
            'mixer', 'is', 'fun'
        ))
        self.assertTrue(user.username in ('mixer', 'is', 'fun'))

        rabbit = mixer.blend(Rabbit, url=mixer.RANDOM)
        self.assertTrue('/' in rabbit.url)

    def test_mix(self):
        from mixer.backend.django import mixer

        test = mixer.blend(Rabbit, title=mixer.MIX.username)
        self.assertEqual(test.title, test.username)

        test = Rabbit.objects.get(pk=test.pk)
        self.assertEqual(test.title, test.username)

        test = mixer.blend(Hole, title=mixer.MIX.owner.title)
        self.assertEqual(test.title, test.owner.title)

        test = mixer.blend(Door, hole__title=mixer.MIX.owner.title)
        self.assertEqual(test.hole.title, test.hole.owner.title)

        test = mixer.blend(Door, hole__title=mixer.MIX.owner.username(
            lambda t: t + 's hole'
        ))
        self.assertTrue(test.hole.owner.username in test.hole.title)
        self.assertTrue('s hole' in test.hole.title)

    def test_contrib(self):
        from mixer.backend.django import mixer

        with self.assertNumQueries(1):
            user = mixer.blend('auth.User')
        self.assertTrue(user)

        with self.assertNumQueries(3):
            customer = mixer.blend(Customer)
        self.assertTrue(customer)

    @staticmethod
    def test_invalid_scheme():
        from mixer.backend.django import mixer
        try:
            mixer.blend('django_app.Unknown')
        except ValueError:
            return False
        raise Exception('test.failed')

    @staticmethod
    def test_invalid_relation():
        from mixer.backend.django import mixer

        try:
            mixer.blend('django_app.Hole', unknown__test=1)
        except ValueError:
            return False
        raise Exception('test.failed')

    def test_generic(self):
        from mixer.backend.django import mixer

        with mixer.ctx(loglevel='INFO'):
            hole = mixer.blend(Hole)
            rabbit = mixer.blend(Rabbit, content_object=hole)
        self.assertEqual(rabbit.object_id, hole.pk)
        self.assertEqual(rabbit.content_type.model_class(), Hole)

    def test_ctx(self):
        from mixer.backend.django import mixer

        with mixer.ctx(commit=False):
            hole = mixer.blend(Hole)
            self.assertTrue(hole)
            self.assertFalse(Hole.objects.count())

        with mixer.ctx(commit=True):
            hole = mixer.blend(Hole)
            self.assertTrue(hole)
            self.assertTrue(Hole.objects.count())


# lint_ignore=F0401,W0401,E0602,W0212,C
