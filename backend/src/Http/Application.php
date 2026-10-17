<?php
declare(strict_types=1);

namespace Aurora\Http;

use Aurora\Exceptions\ApiException;
use Aurora\Http\Controllers\ExerciseController;
use Aurora\Http\Controllers\FitnessStateController;
use Aurora\Http\Controllers\TrainingPlanController;
use JsonException;
use Throwable;

final class Application
{
    private array $controllers;

    public function __construct(
        FitnessStateController $state,
        TrainingPlanController $plans,
        ExerciseController $exercises,
        private array $routes,
    ) {
        $this->controllers = compact('state', 'plans', 'exercises');
    }

    public function handle(string $method, array $query = [], string $rawBody = ''): JsonResponse
    {
        try {
            if (!isset($this->routes[$method])) {
                throw new ApiException(405, ['ok' => false, 'error' => 'Método não permitido']);
            }
            $input = $method === 'POST' ? $this->readBody($rawBody) : $query;
            $action = $input['action'] ?? ($method === 'POST' ? 'save' : '');
            if (!is_string($action)) {
                throw new ApiException(400, ['ok' => false, 'error' => 'Ação inválida']);
            }
            $route = $this->routes[$method][$action] ?? $this->routes[$method]['*'] ?? null;
            if ($route === null) {
                throw new ApiException(400, ['ok' => false, 'error' => 'Ação inválida']);
            }
            [$controller, $operation] = $route;
            return new JsonResponse(200, $this->controllers[$controller]->$operation($input));
        } catch (ApiException $error) {
            return new JsonResponse($error->status, $error->payload);
        } catch (JsonException $error) {
            return new JsonResponse(400, ['ok' => false, 'error' => 'JSON inválido']);
        } catch (Throwable $error) {
            error_log('Fitness API: ' . $error->getMessage());
            return new JsonResponse(500, ['ok' => false, 'error' => 'Falha ao acessar o banco Fitness']);
        }
    }

    private function readBody(string $raw): array
    {
        if (strlen($raw) > 2000000) {
            throw new ApiException(413, ['ok' => false, 'error' => 'Dados ausentes ou acima de 2 MB']);
        }
        $body = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($body)) {
            throw new ApiException(400, ['ok' => false, 'error' => 'Formato de dados inválido']);
        }
        return $body;
    }
}
