# Copyright 2012 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from sqlalchemy import ForeignKey
from sqlalchemy.schema import Column
from sqlalchemy.schema import MetaData

from trove.db.sqlalchemy.migrate_repo.schema import Boolean
from trove.db.sqlalchemy.migrate_repo.schema import create_tables
from trove.db.sqlalchemy.migrate_repo.schema import DateTime
from trove.db.sqlalchemy.migrate_repo.schema import drop_tables
from trove.db.sqlalchemy.migrate_repo.schema import String
from trove.db.sqlalchemy.migrate_repo.schema import Table
from trove.db.sqlalchemy.migrate_repo.schema import Text


meta = MetaData()

scheduledtasks = Table(
    'scheduledtasks',
    meta,
    Column('id', String(36), primary_key=True, nullable=False),
    Column('tenant_id', String(36), nullable=False),
    Column('instance_id', String(36), ForeignKey('instances.id'),
           nullable=False),
    Column('type', String(50), ForeignKey('scheduledtasktypes.type'),
           nullable=False),
    Column('enabled', Boolean(), nullable=False, default=True),
    Column('name', String(255), nullable=False),
    Column('created', DateTime(), nullable=False),
    Column('updated', DateTime()),
    Column('frequency', String(50), nullable=False),
    Column('window_start', DateTime(), nullable=False),
    Column('window_end', DateTime(), nullable=False),
    Column('alert_on_failure', Boolean(), default=False),
    Column('alert_on_success', Boolean(), default=False),
    Column('alert_recipients', Text()),
    Column('description', Text()),
    Column('metadata', Text()),
)


scheduledtasktypes = Table(
    'scheduledtasktypes',
    meta,
    Column('type', String(50), primary_key=True),
    Column('description', Text()),
    Column('enabled', Boolean(), nullable=False, default=True),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    # for some reason we have to load the table before we can FK to it
    Table('instances', meta, autoload=True)
    create_tables([scheduledtasks, scheduledtasktypes])

    scheduledtasktypes.insert().values(
        type='backup',
        enabled=True,
        description="Back up the data store for a specific instance:\n"
        "This will perform a full backup at the scheduled interval "
        "and incremental backups at a reasonable frequency in between",
    ).execute()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    drop_tables([scheduledtasks, scheduledtasktypes])
