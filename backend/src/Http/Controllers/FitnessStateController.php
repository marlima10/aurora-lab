<?php
declare(strict_types=1);

namespace Aurora\Http\Controllers;

use Aurora\Http\Requests\SaveFitnessStateRequest;
use Aurora\Services\FitnessSyncService;

final class FitnessStateController
{
    public function __construct(private FitnessSyncService $service) {}

    public function show(array $input): array
    {
        return $this->service->read();
    }

    public function save(array $input): array
    {
        $state = SaveFitnessStateRequest::validate($input, 'save');
        $revision = isset($input['expectedRevision']) ? (int)$input['expectedRevision'] : null;
        return $this->service->save($state['people'], $state['entries'], $revision);
    }

    public function import(array $input): array
    {
        $state = SaveFitnessStateRequest::validate($input, 'import');
        return $this->service->import($state['people'], $state['entries']);
    }

    public function merge(array $input): array
    {
        $state = SaveFitnessStateRequest::validate($input, 'merge');
        return $this->service->merge($state['people'], $state['entries']);
    }
}
