Exec { path => [ '/bin/', '/sbin/' , '/usr/bin/', '/usr/sbin/' ] }

exec { 'apt-get update':
  command => 'apt-get update',
  timeout => 60,
  tries   => 3
}

package { ['vim', 'python-django', 'python-dateutil']:
  ensure  => 'installed',
  require => Exec['apt-get update'],
}
