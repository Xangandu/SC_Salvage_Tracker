// SC Salvage Tracker — Setup Wizard (Inno Setup 6.7+)
// Layout: Hintergrund install_bg.png, Inhalts-Panel links, Splash rechts sichtbar.
// Hinweis: ParentBackground auf Seiten mit Edits/CheckListBox vermeiden (Controls unsichtbar).

#ifndef MyAppCodename
  #define MyAppCodename "GLOBAL INTERFACE"
#endif

#ifndef MyAppBuild
  #define MyAppBuild "2026.10"
#endif

const
  TRACKER_BG = $12100A;
  TRACKER_PANEL = $271D15;
  TRACKER_TEXT = $FBF7F2;
  TRACKER_ORANGE = $2A7AE0;
  TRACKER_MUTED = $BCA893;
  TRACKER_HINT = $B8A38F;
  TRACKER_BTN_H = 32;
  TRACKER_BTN_GAP = 12;
  TRACKER_BTN_MARGIN = 24;
  TRACKER_BTN_W_NEXT = 136;
  TRACKER_BTN_W_CANCEL = 156;
  TRACKER_BTN_W_BACK = 136;
  TRACKER_BOTTOM_BAR_H = 56;
  { Linkes Panel — rechts bleibt install_bg.png (Splash) sichtbar }
  TRACKER_PANEL_LEFT = 24;
  TRACKER_PANEL_TOP = 58;
  TRACKER_PANEL_WIDTH = 560;
  TRACKER_PAD_L = 16;
  TRACKER_PAD_R = 16;
  TRACKER_TITLE_TOP = 8;
  TRACKER_DESC_TOP = 34;
  TRACKER_BODY_TOP = 62;

function NewLine: String;
begin
  Result := Chr(13) + Chr(10);
end;

function TrackerPanelHeight: Integer;
begin
  Result := WizardForm.ClientHeight - ScaleY(TRACKER_PANEL_TOP) -
    ScaleY(TRACKER_BOTTOM_BAR_H);
end;

function TrackerContentWidth: Integer;
begin
  Result := WizardForm.MainPanel.ClientWidth - ScaleX(TRACKER_PAD_L) -
    ScaleX(TRACKER_PAD_R);
end;

var
  TrackerBgImage: TBitmapImage;
  TrackerAccentStripe: TPanel;
  TrackerBottomBar: TPanel;
  TrackerFooterLabel: TNewStaticText;

procedure WizardFormResized(Sender: TObject); forward;
procedure TrackerStyleInnerPages; forward;

procedure TrackerLockFont(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  L.StyleElements := L.StyleElements - [seFont];
end;

procedure TrackerStyleTitle(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  TrackerLockFont(L);
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 12;
  L.Font.Style := [fsBold];
  L.Font.Color := TRACKER_ORANGE;
end;

procedure TrackerStyleLabel(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  TrackerLockFont(L);
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 10;
  L.Font.Style := [];
  L.Font.Color := TRACKER_TEXT;
end;

procedure TrackerStyleMuted(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  TrackerLockFont(L);
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 9;
  L.Font.Style := [];
  L.Font.Color := TRACKER_MUTED;
end;

procedure TrackerStyleHint(L: TNewStaticText);
begin
  if L = nil then
    Exit;
  TrackerLockFont(L);
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 9;
  L.Font.Style := [];
  L.Font.Color := TRACKER_HINT;
end;

procedure TrackerStyleInput(E: TNewEdit);
begin
  if E = nil then
    Exit;
  E.Font.Name := 'Segoe UI';
  E.Font.Size := 10;
end;

procedure TrackerStyleCheckList(L: TNewCheckListBox);
begin
  if L = nil then
    Exit;
  L.Font.Name := 'Segoe UI';
  L.Font.Size := 10;
end;

procedure TrackerStyleMemo(M: TNewMemo);
begin
  if M = nil then
    Exit;
  M.Font.Name := 'Consolas';
  M.Font.Size := 9;
end;

procedure TrackerApplyPageColors;
begin
  WizardForm.Color := TRACKER_BG;
  WizardForm.MainPanel.Color := TRACKER_PANEL;
  WizardForm.MainPanel.ParentBackground := False;
  WizardForm.WelcomePage.Color := TRACKER_PANEL;
  WizardForm.WelcomePage.ParentBackground := False;
  WizardForm.InnerPage.Color := TRACKER_PANEL;
  WizardForm.InnerPage.ParentBackground := False;
  WizardForm.FinishedPage.Color := TRACKER_PANEL;
  WizardForm.FinishedPage.ParentBackground := False;
end;

procedure TrackerLayoutMainPanel;
begin
  WizardForm.MainPanel.SetBounds(
    ScaleX(TRACKER_PANEL_LEFT),
    ScaleY(TRACKER_PANEL_TOP),
    ScaleX(TRACKER_PANEL_WIDTH),
    TrackerPanelHeight);
end;

procedure TrackerLayoutAccentStripe;
begin
  if TrackerAccentStripe = nil then
    Exit;
  TrackerAccentStripe.SetBounds(
    WizardForm.MainPanel.Left,
    WizardForm.MainPanel.Top,
    ScaleX(4),
    WizardForm.MainPanel.Height);
end;

procedure TrackerLayoutPageHeaders;
var
  PadL, W: Integer;
begin
  PadL := ScaleX(TRACKER_PAD_L);
  W := TrackerContentWidth;

  WizardForm.PageNameLabel.AutoSize := False;
  WizardForm.PageNameLabel.SetBounds(
    PadL, ScaleY(TRACKER_TITLE_TOP), W, ScaleY(22));

  WizardForm.PageDescriptionLabel.AutoSize := False;
  WizardForm.PageDescriptionLabel.SetBounds(
    PadL, ScaleY(TRACKER_DESC_TOP), W, ScaleY(24));
end;

procedure TrackerLayoutWelcomePage;
var
  PadL, W: Integer;
begin
  PadL := ScaleX(TRACKER_PAD_L);
  W := TrackerContentWidth;

  WizardForm.WelcomeLabel1.AutoSize := False;
  WizardForm.WelcomeLabel1.SetBounds(
    PadL, ScaleY(TRACKER_TITLE_TOP), W, ScaleY(22));

  WizardForm.WelcomeLabel2.AutoSize := False;
  WizardForm.WelcomeLabel2.SetBounds(
    PadL, ScaleY(TRACKER_DESC_TOP), W,
    WizardForm.WelcomePage.Height - ScaleY(TRACKER_DESC_TOP) - ScaleY(12));
end;

procedure TrackerLayoutFinishedPage;
var
  PadL, W: Integer;
begin
  PadL := ScaleX(TRACKER_PAD_L);
  W := TrackerContentWidth;

  WizardForm.FinishedLabel.AutoSize := False;
  WizardForm.FinishedLabel.SetBounds(
    PadL, ScaleY(TRACKER_TITLE_TOP), W,
    WizardForm.FinishedPage.Height - ScaleY(TRACKER_TITLE_TOP) - ScaleY(12));
end;

procedure TrackerLayoutSelectDirPage;
var
  PadL, W, Y, EditW: Integer;
begin
  PadL := ScaleX(TRACKER_PAD_L);
  W := TrackerContentWidth;
  EditW := W - ScaleX(138);
  if EditW < ScaleX(200) then
    EditW := ScaleX(200);
  Y := ScaleY(TRACKER_BODY_TOP);

  WizardForm.SelectDirLabel.AutoSize := False;
  WizardForm.SelectDirLabel.SetBounds(PadL, Y, W, ScaleY(24));
  Y := Y + ScaleY(28);

  WizardForm.DirEdit.SetBounds(PadL, Y, EditW, ScaleY(23));
  WizardForm.DirBrowseButton.SetBounds(
    PadL + EditW + ScaleX(8), Y, ScaleX(130), ScaleY(23));
  Y := Y + ScaleY(30);

  WizardForm.SelectDirBrowseLabel.AutoSize := False;
  WizardForm.SelectDirBrowseLabel.SetBounds(PadL, Y, W, ScaleY(32));
  Y := Y + ScaleY(34);

  WizardForm.DiskSpaceLabel.AutoSize := False;
  WizardForm.DiskSpaceLabel.SetBounds(PadL, Y, W, ScaleY(18));
end;

procedure TrackerLayoutTasksPage;
var
  PadL, W, Y: Integer;
begin
  PadL := ScaleX(TRACKER_PAD_L);
  W := TrackerContentWidth;
  Y := ScaleY(TRACKER_BODY_TOP);

  WizardForm.SelectTasksLabel.AutoSize := False;
  WizardForm.SelectTasksLabel.SetBounds(PadL, Y, W, ScaleY(18));
  Y := Y + ScaleY(22);

  WizardForm.TasksList.SetBounds(
    PadL, Y, W,
    WizardForm.InnerPage.Height - Y - ScaleY(12));
end;

procedure TrackerLayoutReadyPage;
var
  PadL, W, Y: Integer;
begin
  PadL := ScaleX(TRACKER_PAD_L);
  W := TrackerContentWidth;
  Y := ScaleY(TRACKER_BODY_TOP);

  WizardForm.ReadyLabel.AutoSize := False;
  WizardForm.ReadyLabel.SetBounds(PadL, Y, W, ScaleY(22));
  Y := Y + ScaleY(26);

  WizardForm.ReadyMemo.SetBounds(
    PadL, Y, W,
    WizardForm.InnerPage.Height - Y - ScaleY(12));
end;

procedure TrackerLayoutInstallingPage;
var
  PadL, W, Y: Integer;
begin
  PadL := ScaleX(TRACKER_PAD_L);
  W := TrackerContentWidth;
  Y := ScaleY(TRACKER_BODY_TOP);

  WizardForm.StatusLabel.AutoSize := False;
  WizardForm.StatusLabel.SetBounds(PadL, Y, W, ScaleY(22));
  Y := Y + ScaleY(28);

  WizardForm.ProgressGauge.SetBounds(PadL, Y, W, ScaleY(18));
  Y := Y + ScaleY(26);

  WizardForm.FilenameLabel.AutoSize := False;
  WizardForm.FilenameLabel.SetBounds(PadL, Y, W, ScaleY(18));
end;

procedure TrackerStyleInnerPages;
begin
  WizardForm.WizardSmallBitmapImage.Visible := False;

  WizardForm.SelectDirLabel.Caption :=
    'Der Salvage Tracker wird in folgenden Ordner installiert:';
  WizardForm.SelectDirBrowseLabel.Caption :=
    'Klicke auf Weiter, um fortzufahren — oder auf Durchsuchen, ' +
    'um einen anderen Ordner zu wählen.';
  WizardForm.DirBrowseButton.Caption := 'DURCHSUCHEN …';

  WizardForm.SelectDirLabel.Visible := True;
  WizardForm.SelectDirBrowseLabel.Visible := True;
  WizardForm.DirEdit.Visible := True;
  WizardForm.DirBrowseButton.Visible := True;
  WizardForm.DiskSpaceLabel.Visible := True;

  WizardForm.SelectTasksLabel.Visible := True;
  WizardForm.TasksList.Visible := True;
  WizardForm.ReadyLabel.Visible := True;
  WizardForm.ReadyMemo.Visible := True;
  WizardForm.StatusLabel.Visible := True;
  WizardForm.ProgressGauge.Visible := True;
  WizardForm.FilenameLabel.Visible := True;
end;

procedure TrackerApplyPageTheme;
begin
  TrackerApplyPageColors;

  TrackerStyleTitle(WizardForm.WelcomeLabel1);
  TrackerStyleLabel(WizardForm.WelcomeLabel2);
  TrackerStyleTitle(WizardForm.FinishedLabel);
  TrackerStyleHint(WizardForm.PageDescriptionLabel);
  TrackerStyleTitle(WizardForm.PageNameLabel);

  TrackerStyleLabel(WizardForm.StatusLabel);
  TrackerStyleHint(WizardForm.FilenameLabel);
  TrackerStyleLabel(WizardForm.SelectDirLabel);
  TrackerStyleHint(WizardForm.SelectDirBrowseLabel);
  TrackerStyleHint(WizardForm.SelectTasksLabel);
  TrackerStyleLabel(WizardForm.ReadyLabel);
  TrackerStyleLabel(WizardForm.PreparingLabel);
  TrackerStyleMuted(WizardForm.DiskSpaceLabel);

  TrackerStyleInput(WizardForm.DirEdit);
  TrackerStyleCheckList(WizardForm.TasksList);
  TrackerStyleMemo(WizardForm.ReadyMemo);

  WizardForm.BackButton.Caption := '◂ ZURÜCK';
  WizardForm.NextButton.Caption := 'WEITER ▸';
  WizardForm.CancelButton.Caption := 'ABBRECHEN';

  WizardForm.WizardBitmapImage.Visible := False;
  WizardForm.WizardSmallBitmapImage.Visible := False;
  WizardForm.BeveledLabel.Visible := False;

  TrackerStyleInnerPages;

  if TrackerFooterLabel <> nil then
  begin
    TrackerFooterLabel.Caption :=
      ExpandConstant('{#MyAppCodename}') + ' · Build ' +
      ExpandConstant('{#MyAppBuild}') +
      ' · SC Salvage Tracker Setup';
    TrackerStyleMuted(TrackerFooterLabel);
  end;
end;

procedure TrackerLayoutButtons;
var
  TopPos, RightPos: Integer;
begin
  TopPos := WizardForm.ClientHeight - TRACKER_BOTTOM_BAR_H +
    ((TRACKER_BOTTOM_BAR_H - TRACKER_BTN_H) div 2);

  RightPos := WizardForm.ClientWidth - TRACKER_BTN_MARGIN;
  WizardForm.CancelButton.SetBounds(
    RightPos - TRACKER_BTN_W_CANCEL, TopPos,
    TRACKER_BTN_W_CANCEL, TRACKER_BTN_H);

  RightPos := RightPos - TRACKER_BTN_W_CANCEL - TRACKER_BTN_GAP;
  WizardForm.NextButton.SetBounds(
    RightPos - TRACKER_BTN_W_NEXT, TopPos,
    TRACKER_BTN_W_NEXT, TRACKER_BTN_H);

  if WizardForm.BackButton.Visible then
  begin
    RightPos := RightPos - TRACKER_BTN_W_NEXT - TRACKER_BTN_GAP;
    WizardForm.BackButton.SetBounds(
      RightPos - TRACKER_BTN_W_BACK, TopPos,
      TRACKER_BTN_W_BACK, TRACKER_BTN_H);
  end;

  WizardForm.BackButton.BringToFront;
  WizardForm.NextButton.BringToFront;
  WizardForm.CancelButton.BringToFront;
end;

procedure TrackerLayoutWizard;
begin
  if TrackerBgImage <> nil then
  begin
    TrackerBgImage.SetBounds(
      0, 0, WizardForm.ClientWidth, WizardForm.ClientHeight);
    TrackerBgImage.SendToBack;
  end;

  TrackerLayoutMainPanel;
  TrackerLayoutAccentStripe;

  if WizardForm.CurPageID = wpWelcome then
    TrackerLayoutWelcomePage
  else if WizardForm.CurPageID = wpFinished then
    TrackerLayoutFinishedPage
  else if WizardForm.CurPageID = wpSelectDir then
  begin
    TrackerLayoutPageHeaders;
    TrackerLayoutSelectDirPage;
  end
  else if WizardForm.CurPageID = wpSelectTasks then
  begin
    TrackerLayoutPageHeaders;
    TrackerLayoutTasksPage;
  end
  else if WizardForm.CurPageID = wpReady then
  begin
    TrackerLayoutPageHeaders;
    TrackerLayoutReadyPage;
  end
  else if WizardForm.CurPageID = wpInstalling then
  begin
    TrackerLayoutPageHeaders;
    TrackerLayoutInstallingPage;
  end
  else
    TrackerLayoutPageHeaders;

  if TrackerAccentStripe <> nil then
    TrackerAccentStripe.BringToFront;
  WizardForm.MainPanel.BringToFront;

  if TrackerFooterLabel <> nil then
  begin
    TrackerFooterLabel.SetBounds(
      ScaleX(24),
      WizardForm.ClientHeight - TRACKER_BOTTOM_BAR_H +
        ((TRACKER_BOTTOM_BAR_H - 18) div 2),
      ScaleX(460), ScaleY(18));
    TrackerFooterLabel.BringToFront;
  end;

  if TrackerBottomBar <> nil then
  begin
    TrackerBottomBar.SetBounds(
      0, WizardForm.ClientHeight - TRACKER_BOTTOM_BAR_H,
      WizardForm.ClientWidth, TRACKER_BOTTOM_BAR_H);
    TrackerBottomBar.SendToBack;
  end;

  TrackerLayoutButtons;
end;

procedure TrackerUpdateHeader;
begin
  case WizardForm.CurPageID of
    wpWelcome:
      begin
        WizardForm.WelcomeLabel1.Caption := 'Willkommen';
        WizardForm.WelcomeLabel2.Caption :=
          'Schritt 1 von 6 · Der Assistent führt dich durch die Installation.' +
          NewLine + NewLine +
          'Dieser Assistent richtet den Salvage Tracker auf deinem PC ein — ' +
          'Sitzungen, Raffinerie, Verkäufe, Lager und Crew-Auszahlung.' +
          NewLine + NewLine +
          'Edition: ' + ExpandConstant('{#MyAppName}') + NewLine + NewLine +
          'Klicke auf Weiter, um fortzufahren.';
      end;
    wpSelectDir:
      begin
        WizardForm.PageNameLabel.Caption := 'Installationsordner';
        WizardForm.PageDescriptionLabel.Caption :=
          'Schritt 2 von 6 · Wähle den Zielordner.';
      end;
    wpSelectTasks:
      begin
        WizardForm.PageNameLabel.Caption := 'Zusätzliche Optionen';
        WizardForm.PageDescriptionLabel.Caption :=
          'Schritt 3 von 6 · Verknüpfungen und Startverhalten.';
      end;
    wpReady:
      begin
        WizardForm.PageNameLabel.Caption := 'Bereit zur Installation';
        WizardForm.PageDescriptionLabel.Caption :=
          'Schritt 4 von 6 · Einstellungen prüfen und installieren.';
      end;
    wpInstalling:
      begin
        WizardForm.PageNameLabel.Caption := 'Installation läuft';
        WizardForm.PageDescriptionLabel.Caption :=
          'Schritt 5 von 6 · Dateien werden entpackt — bitte warten …';
      end;
    wpFinished:
      begin
        WizardForm.FinishedLabel.Caption :=
          'Installation abgeschlossen' + NewLine + NewLine +
          'Schritt 6 von 6 · Der Salvage Tracker ist bereit.' + NewLine + NewLine +
          'Starte die Anwendung über das Startmenü oder die Desktop-Verknüpfung.';
      end;
  end;
end;

function InitializeSetup(): Boolean;
begin
  ExtractTemporaryFile('install_bg.png');
  Result := True;
end;

procedure InitializeWizard();
begin
  WizardForm.ClientWidth := ScaleX(920);
  WizardForm.ClientHeight := ScaleY(580);
  WizardForm.Position := poScreenCenter;

  TrackerBgImage := TBitmapImage.Create(WizardForm);
  TrackerBgImage.Parent := WizardForm;
  TrackerBgImage.Stretch := True;
  TrackerBgImage.AutoSize := False;
  TrackerBgImage.BackColor := TRACKER_BG;
  try
    TrackerBgImage.Bitmap.LoadFromFile(
      ExpandConstant('{tmp}\install_bg.png'));
  except
    TrackerBgImage.Visible := False;
  end;

  TrackerAccentStripe := TPanel.Create(WizardForm);
  TrackerAccentStripe.Parent := WizardForm;
  TrackerAccentStripe.Color := TRACKER_ORANGE;
  TrackerAccentStripe.BevelOuter := bvNone;
  TrackerAccentStripe.BevelInner := bvNone;
  TrackerAccentStripe.ParentBackground := False;

  TrackerBottomBar := TPanel.Create(WizardForm);
  TrackerBottomBar.Parent := WizardForm;
  TrackerBottomBar.Color := TRACKER_BG;
  TrackerBottomBar.BevelOuter := bvNone;
  TrackerBottomBar.BevelInner := bvNone;
  TrackerBottomBar.ParentBackground := False;

  TrackerFooterLabel := TNewStaticText.Create(WizardForm);
  TrackerFooterLabel.Parent := WizardForm;
  TrackerFooterLabel.AutoSize := False;

  TrackerApplyPageTheme();
  TrackerLayoutWizard();
  TrackerUpdateHeader();

  WizardForm.OnResize := @WizardFormResized;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  TrackerApplyPageTheme();
  TrackerUpdateHeader();
  TrackerLayoutWizard();

  if CurPageID = wpReady then
    WizardForm.NextButton.Caption := 'INSTALLIEREN ▸'
  else if CurPageID = wpFinished then
    WizardForm.NextButton.Caption := 'FERTIGSTELLEN'
  else if CurPageID <> wpInstalling then
    WizardForm.NextButton.Caption := 'WEITER ▸';

  TrackerLayoutButtons;
end;

procedure WizardFormResized(Sender: TObject);
begin
  TrackerLayoutWizard();
  TrackerApplyPageTheme();
end;

procedure DeinitializeWizard();
begin
  TrackerBgImage := nil;
  TrackerAccentStripe := nil;
  TrackerBottomBar := nil;
  TrackerFooterLabel := nil;
end;
