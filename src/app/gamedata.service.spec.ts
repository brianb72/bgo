import { TestBed } from '@angular/core/testing';

import { GamedataService } from './gamedata.service';

describe('GamedataService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: GamedataService = TestBed.get(GamedataService);
    expect(service).toBeTruthy();
  });
});
