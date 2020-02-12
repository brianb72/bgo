import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { NextMove } from './nextmove-interface';


@Injectable({
  providedIn: 'root'
})

export class GamedataService {
  private apiBaseUrl = environment.apiBaseUrl;

  constructor(private httpClient: HttpClient) { }

  public getNextMoveData(moveList): Observable<NextMove[]> {
    const url: string = `${this.apiBaseUrl}/nextmove/${moveList}`;
    return this.httpClient
      .get<NextMove[]>(url);
  }
}
