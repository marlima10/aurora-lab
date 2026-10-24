# Loaded only by the optional SSO overlay, after Devise/Warden.
require 'active_support/security_utils'

class AuroraSsoMiddleware
  def initialize(app)
    @app = app
    @secret = ENV.fetch('AURORA_SSO_SECRET')
    raise 'Configure a private SSO secret' if @secret.length < 32
  end

  def call(env)
    return @app.call(env) if env['PATH_INFO'] == '/health'
    supplied = env['HTTP_X_AURORA_PROXY_SECRET'].to_s
    unless ActiveSupport::SecurityUtils.secure_compare(supplied, @secret)
      return [403, {'content-type' => 'text/plain', 'cache-control' => 'no-store'}, ['SSO required']]
    end
    identity = env['HTTP_X_AURORA_IDENTITY'].to_s
    user = User.find_by(email: identity)
    return [403, {'content-type' => 'text/plain'}, ['Mapped user not found']] unless user
    if user.respond_to?(:active_for_authentication?) && !user.active_for_authentication?
      return [403, {'content-type' => 'text/plain'}, ['Mapped user is not active']]
    end
    # No creation, role promotion or data migration. Re-evaluate the identity on every request.
    env.fetch('warden').set_user(user, store: false)
    @app.call(env)
  end
end

Rails.application.config.middleware.insert_after Warden::Manager, AuroraSsoMiddleware
