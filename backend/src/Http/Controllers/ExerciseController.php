<?php
declare(strict_types=1);

namespace Aurora\Http\Controllers;

use Aurora\Exceptions\ValidationException;
use Aurora\Http\Requests\SaveExerciseRequest;
use Aurora\Services\ExerciseCatalogService;

final class ExerciseController
{
    public function __construct(private ExerciseCatalogService $service) {}

    public function index(array $input): array
    {
        return $this->service->list();
    }

    public function save(array $input): array
    {
        return $this->service->save(SaveExerciseRequest::validate($input));
    }

    public function delete(array $input): array
    {
        $id = $input['id'] ?? null;
        if (!is_string($id) || $id === '') {
            throw new ValidationException('Exercício não informado');
        }
        return $this->service->delete($id);
    }
}
