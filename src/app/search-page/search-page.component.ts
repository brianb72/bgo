import { Component, OnInit } from '@angular/core';
import { GamedataService } from '../gamedata.service';
import { NextMove } from '../nextmove-interface';

@Component({
  selector: 'app-search-page',
  templateUrl: './search-page.component.html',
  styleUrls: ['./search-page.component.css']
})
export class SearchPageComponent implements OnInit {
  nextmoves: NextMove[];
  title: 'Next Moves';

  constructor(private gamedataService: GamedataService) { }

  doSearch() {
    this.gamedataService
      .getNextMoveData('pd+dp')
      .subscribe((data) =>  {
        this.nextmoves = data;
        console.log(this.nextmoves)
      });

  }

  ngOnInit() {
      this.doSearch();
  }

}
