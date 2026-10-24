# Synthetic Rack/Warden identities; no Rails database or production account is loaded.
require 'ostruct'
module Warden; class Manager; end; end
module Rails
  def self.application
    middleware = Object.new
    def middleware.insert_after(*args); end
    OpenStruct.new(config: OpenStruct.new(middleware: middleware))
  end
end
class User
  attr_reader :email, :role
  def initialize(email,active=true); @email=email; @role=:reader; @active=active; end
  def active_for_authentication?; @active; end
  def self.find_by(email:); {'mapped@example.test'=>new('mapped@example.test'), 'disabled@example.test'=>new('disabled@example.test',false)}[email]; end
end
class Identity
  attr_reader :user
  def set_user(user,store:); raise 'Persistent native session requested' if store; @user=user; end
end
ENV['AURORA_SSO_SECRET']='fixture-private-proxy-secret-000000000'
load File.join(__dir__, 'manyfold.rb')
app=AuroraSsoMiddleware.new(->(env){[200,{},[env['warden'].user.email]]})
env={'PATH_INFO'=>'/', 'HTTP_X_AURORA_PROXY_SECRET'=>ENV.fetch('AURORA_SSO_SECRET'), 'HTTP_X_AURORA_IDENTITY'=>'mapped@example.test', 'warden'=>Identity.new}
raise 'Mapping failed' unless app.call(env).first==200 && env['warden'].user.role==:reader
raise 'Forged secret accepted' unless app.call(env.merge('HTTP_X_AURORA_PROXY_SECRET'=>'forged')).first==403
raise 'Unknown user accepted' unless app.call(env.merge('HTTP_X_AURORA_IDENTITY'=>'unknown@example.test')).first==403
raise 'Disabled user accepted' unless app.call(env.merge('HTTP_X_AURORA_IDENTITY'=>'disabled@example.test')).first==403
puts 'Manyfold middleware: 4 synthetic identity assertions passed'
